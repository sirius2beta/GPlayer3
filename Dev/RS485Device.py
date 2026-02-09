import time
import serial
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import struct
import logging
import threading

from Dev.Device import Device
from config import Config as CF

SENSOR = b'\x04'
node1_control_type = 2 # sonar control type: 2
node2_control_type = 0 # winch control type: 0
class RS485Device(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list = [], networkManager = None):
        try:
            super().__init__(device_type, dev_path, sensor_group_list, networkManager)
            self.client = ModbusSerialClient(
                port=self.dev_path,
                baudrate=19200,
                parity='E',
                stopbits=1,
                bytesize=8,
                timeout=1
            )
            self.client.connect()
            self.node1_addr = 0x11
            self.node2_addr = 0x12

            self.node1Connected = False
            self.node2Connected = False

            self.isSerialInit = True
            self.sonarPWR = 0
            self.status_code = 1

            self.aqua_data = [0.0] * 21
            
            logging.info("RS485Device: Connected to RS485 device.") 
        except Exception as e:
            logging.info(f"   [X] RS485Device failed to start")
            raise e
        logging.info("   [O] RS485Device initialized")
    def setToolBox(self, toolBox):
        self._toolBox = toolBox
        threading.Thread(target = self.reader, daemon = True).start() # start the reader thread
    def close(self):
        self.client.close()
    
    # ---------- Node 1 (Sonar) ----------

    def setSonarPWR(self, on: bool):
        try:
            coil_addr = 0  
            self.client.write_coil(coil_addr, on, device_id=self.node1_addr)
            self.sonarPWR = 1 if on else 0
            logging.info(f"RS485Device: [Node1] Set sonar {'ON' if on else 'OFF'}")
            self.node1Connected = True
        except ModbusException as e:
            logging.info(f"RS485Device: [Node1] Set sonar failed: {e}")
            self.node1Connected = False

    # ---------- Node 2 (Motor Controller) ----------

    def stopMotor(self):
        try:
            coil_addr = 0  
            self.client.write_coil(coil_addr, False, device_id=self.node2_addr)
            logging.info(f"RS485Device: [Node2] stop motor")
        except ModbusException as e:
            logging.info(f"RS485Device: [Node2] Set motor failed: {e}")
            self.node2Connected = False

    def setMaxSpeed(self, speed):
        try:
            self.client.write_register(0, speed, device_id=self.node2_addr)
            logging.info(f"RS485Device: [Node2] Set MaxSpeed = {speed}")
        except ModbusException as e:
            logging.info(f"RS485Device: [Node2] Set MaxSpeed failed: {e}")
            self.node2Connected = False

    def setAcc(self, acc):
        try:
            self.client.write_register(1, acc, device_id=self.node2_addr)
            logging.info(f"RS485Device: [Node2] Set Acc = {acc}")
        except ModbusException as e:
            logging.info(f"RS485Device: [Node2] Set Acc failed: {e}")
            self.node2Connected = False

    def setTensionThreshold(self, tension):
        try:
            high = (tension >> 16) & 0xFFFF
            low = tension & 0xFFFF
            self.client.write_registers(2, [high, low], device_id=self.node2_addr)
            logging.info(f"RS485Device: [Node2] Set Tension Threshold = {tension}")
        except ModbusException as e:
            logging.info(f"RS485Device: [Node2] Set Tension Threshold failed: {e}")
            self.node2Connected = False

    def getCurrentStep(self):
        try:
            result = self.client.read_input_registers(8, count=2, device_id=self.node2_addr)
            if result.isError():
                logging.info("RS485Device: [Node2] Get Current Step failed")
            else:
                high, low = result.registers
                step = (high << 16) | low
                if step & 0x80000000:  # 補 signed
                    step -= 0x100000000
                logging.info(f"RS485Device: [Node2] Current Step = {step}")
                return step
        except ModbusException as e:
            logging.info(f"[Node2] Get Current Step failed: {e}")
            self.node2Connected = False
        return None

    def setCurrentStep(self, step):
        try:
            high = (step >> 16) & 0xFFFF
            low = step & 0xFFFF
            self.client.write_registers(6, [high, low], device_id=self.node2_addr)
            logging.info(f"RS485Device: [Node2] Set Current Step = {step}")
        except ModbusException as e:
            logging.info(f"RS485Device: [Node2] Set Current Step failed: {e}")
            self.node2Connected = False

    def setTargetStep(self, step):
        try:
            high = (step >> 16) & 0xFFFF
            low = step & 0xFFFF
            # ESP 定義在 Hreg[4] → 40005
            self.client.write_registers(4, [high, low], device_id=self.node2_addr)
            logging.info(f"RS485Device: [Node2] Set Target Step = {step}")
        except ModbusException as e:
            logging.info(f"RS485Device: [Node2] Set Target Step failed: {e}")
            self.node2Connected = False

    def getStatus(self):
        # read 30006~30010 (currentTension(32bit), currentStep(32bit), isRunning(16bit))
        runningState = 0x00
        try:
            result = self.client.read_input_registers(6, count=5, device_id=self.node2_addr)
            if result.isError():
                logging.info("RS485Device: [Node2] Get Status failed")
                return None
            else:
                regs = result.registers
                tension = (regs[0] << 16) | regs[1]
                step = (regs[2] << 16) | regs[3]
                if step & 0x80000000:  # 補 signed
                    step -= 0x100000000
                runningState = regs[4]
                #logging.info(f"[Node2] Status - Tension: {tension}, Step: {step}, RunningState: {'Running' if runningState==0xFF else 'Stopped'}")
                tension = (regs[0] << 16) | regs[1]
                if runningState == 0:
                    status = 0
                else:
                    status = 1

                data = struct.pack("<B", node2_control_type)
                data += struct.pack("<B", 8)
                data += struct.pack("<i", step)
                data += struct.pack("<i", tension)
                data += struct.pack("<B", status)
                self.networkManager.sendMsg(b'\x05', data)
                
                return tension, step
        except ModbusException as e:
            logging.info(f"RS485Device: [Node2] Get Status failed: {e}")
            self.node2Connected = False
        return None
        
    def get_aqua_data(self):
        # read input registers from 20, all 21 sensors, convert to 32-bit float
        try:
            result = self.client.read_input_registers(20, count=42, device_id=self.node2_addr)
            if result.isError():
                logging.info("RS485Device: [Node2] Get Aqua Data failed")
                self.node2Connected = False
                self.status_code = 0
                return None
            else:
                regs = result.registers
                aqua_data = []
                for i in range(0, 42, 2):
                    high = regs[i]
                    low = regs[i+1]
                    combined = (high << 16) | low
                    float_value = struct.unpack('>f', struct.pack('>I', combined))[0]
                    aqua_data.append(float_value)
                    self.aqua_data[i//2] = float_value # store the data in the aqua_data list
                    #save to sensor group 1
                    if i//2 < len(self.sensor_group_list[1].get_all()):
                        self.sensor_group_list[1].get_sensor(i//2).data = float_value
                self.networkManager.sendMsg(SENSOR, self.sensor_group_list[1].pack()) # send the data to the network manager
                    
                
                logging.info(f"[Node2] Aqua Data: {aqua_data}")
                self.status_code = 2
                return aqua_data
        except ModbusException as e:
            logging.info(f"RS485Device: [Node2] Get Aqua Data failed: {e}")
            self.node2Connected = False
            return None

    def testMotorManuver(self):
        self.setMaxSpeed(2000)
        time.sleep(0.5)
        self.setAcc(500)
        time.sleep(0.5)
        self.setTensionThreshold(-1500)
        time.sleep(0.5)
        self.getCurrentStep()
        time.sleep(0.5)
        self.setCurrentStep(0)
        time.sleep(1)
        
        count = 0
        target = -10000
        while True:
            if count ==9:
                count = 0
                target = -target
                self.stopMotor()
                time.sleep(0.5)
            self.setTargetStep(target)
            self.getStatus()
            
            count += 1
            time.sleep(1)
    def testAqua(self):
        while True:
            self.get_aqua_data()
            time.sleep(2)
    def testSonar(self):
        while True:
            self.setSonarPWR(True)
            time.sleep(5)
            self.setSonarPWR(False)
            time.sleep(5)
    def testStatus(self):
        while True:
            self.getStatus()
            time.sleep(2)
    
    # process command for control
    def processCMD(self, control_type ,cmd):
        if self.isSerialInit == False:
            return
        if control_type == node2_control_type:
            command_type = int(cmd[0])
            logging.info(f"RS485Device: control:{control_type}, command type:{command_type}, ")
            if command_type == 0:  # 讀取全部參數
                logging.info("  - set")
                # 待新增
            elif command_type == 1:  # 讀取部分參數
                pass
            elif command_type == 2:  # 寫入全部參數
                pass

            elif command_type == 3: #寫入部分參數
                index = int(cmd[1])
                logging.info(f"RS485Device: write index:{index}")
                if index == 0: #maxspeed
                    maxSpeed = int(struct.unpack("<I", cmd[2:])[0])
                    if maxSpeed>2000: #  maxspeed cant exceed 2000
                        pass
                    # set maxspeed and acc
                    self.setMaxSpeed(maxSpeed)
                    time.sleep(0.1)
                    self.setAcc(maxSpeed/2)
                    logging.info(f"RS485Device: set maxspeed:{maxSpeed}")

            elif command_type == 4: #回傳全部參數
                pass
            elif command_type == 5: #回傳部分參數
                pass
            elif command_type == 6: #move
                step = int(struct.unpack("<i", cmd[1:])[0])
                logging.info(f"RS485Device: [Winch] move step {step}")
                if self.isSerialInit == True:
                    self.setTargetStep(step)
            elif command_type == 7: #stop
                self.stopMotor()
                logging.info("RS485Device: [Winch] stop")
            elif command_type == 8: # report step tension
                pass
            elif command_type == 9: # reset position
                self.setCurrentStep(0)
                logging.info("RS485Device: [winch] reset")
        elif control_type == 2:
            logging.info("RS485Device: SonarDevice::getMsg")
            command_type = int(cmd[0])
            logging.info(f"RS485Device: control:{control_type}, command type:{command_type}, ")
            if command_type == 0:  # 讀取全部參數
                pass
            elif command_type == 1:  # 讀取部分參數
                pass
            elif command_type == 2:  # 寫入全部參數
                pass
            elif command_type == 3: #寫入部分參數
                pass
            elif command_type == 4: #回傳全部參數
                pass
            elif command_type == 5: #回傳部分參數
                pass
            elif command_type == 6: #power
                self.power = cmd[1]
                if self.power == 1:
                    self.setSonarPWR(True)
                    logging.info("power on")
                else:
                    self.setSonarPWR(False)
                    logging.info("power off")
            elif command_type == 7: #power
                data = struct.pack("<B", 2)
                data += struct.pack("<B", 7)
                data += struct.pack("<B", self.power)
                self.networkManager.sendMsg(b'\x05', data)

    def _io_loop(self):
        
            step = 0
            tension = 0
            status = 0
            while True:
                self.getStatus()
                time.sleep(0.2)
                
    def reader(self): # read data from the device and store it in the data_list.
        while True:
            self.get_aqua_data()
            time.sleep(1)