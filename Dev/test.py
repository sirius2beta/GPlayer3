from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import time
import struct

class RS485Master:
    def __init__(self, port: str):
        self.client = ModbusSerialClient(
            port=port,
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

    def close(self):
        self.client.close()
    
    # ---------- Node 1 (Sonar) ----------

    def setSonarPWR(self, on: bool):
        try:
            coil_addr = 0  
            self.client.write_coil(coil_addr, on, device_id=self.node1_addr)
            print(f"[Node1] Set sonar {'ON' if on else 'OFF'}")
            self.node1Connected = True
        except ModbusException as e:
            print(f"[Node1] Set sonar failed: {e}")
            self.node1Connected = False

    # ---------- Node 2 (Motor Controller) ----------

    def stopMotor(self):
        try:
            coil_addr = 0  
            self.client.write_coil(coil_addr, False, device_id=self.node2_addr)
            print(f"[Node2] stop motor")
        except ModbusException as e:
            print(f"[Node2] Set motor failed: {e}")
            self.node2Connected = False

    def setMaxSpeed(self, speed):
        try:
            self.client.write_register(0, speed, device_id=self.node2_addr)
            print(f"[Node2] Set MaxSpeed = {speed}")
        except ModbusException as e:
            print(f"[Node2] Set MaxSpeed failed: {e}")
            self.node2Connected = False

    def setAcc(self, acc):
        try:
            self.client.write_register(1, acc, device_id=self.node2_addr)
            print(f"[Node2] Set Acc = {acc}")
        except ModbusException as e:
            print(f"[Node2] Set Acc failed: {e}")
            self.node2Connected = False

    def setTensionThreshold(self, tension):
        try:
            high = (tension >> 16) & 0xFFFF
            low = tension & 0xFFFF
            self.client.write_registers(2, [high, low], device_id=self.node2_addr)
            print(f"[Node2] Set Tension Threshold = {tension}")
        except ModbusException as e:
            print(f"[Node2] Set Tension Threshold failed: {e}")
            self.node2Connected = False

    def getCurrentStep(self):
        try:
            result = self.client.read_input_registers(8, count=2, device_id=self.node2_addr)
            if result.isError():
                print("[Node2] Get Current Step failed")
            else:
                high, low = result.registers
                step = (high << 16) | low
                if step & 0x80000000:  # 補 signed
                    step -= 0x100000000
                print(f"[Node2] Current Step = {step}")
                return step
        except ModbusException as e:
            print(f"[Node2] Get Current Step failed: {e}")
            self.node2Connected = False
        return None

    def setCurrentStep(self, step):
        try:
            high = (step >> 16) & 0xFFFF
            low = step & 0xFFFF
            self.client.write_registers(6, [high, low], device_id=self.node2_addr)
            print(f"[Node2] Set Current Step = {step}")
        except ModbusException as e:
            print(f"[Node2] Set Current Step failed: {e}")
            self.node2Connected = False

    def setTargetStep(self, step):
        try:
            high = (step >> 16) & 0xFFFF
            low = step & 0xFFFF
            # ESP 定義在 Hreg[4] → 40005
            self.client.write_registers(4, [high, low], device_id=self.node2_addr)
            print(f"[Node2] Set Target Step = {step}")
        except ModbusException as e:
            print(f"[Node2] Set Target Step failed: {e}")
            self.node2Connected = False

    def getStatus(self):
        # read 30006~30010 (currentTension(32bit), currentStep(32bit), isRunning(16bit))
        runningState = 0x00
        try:
            result = self.client.read_input_registers(6, count=5, device_id=self.node2_addr)
            if result.isError():
                print("[Node2] Get Status failed")
                return None
            else:
                regs = result.registers
                tension = (regs[0] << 16) | regs[1]
                step = (regs[2] << 16) | regs[3]
                if step & 0x80000000:  # 補 signed
                    step -= 0x100000000
                runningState = regs[4]
                print(f"[Node2] Status - Tension: {tension}, Step: {step}, RunningState: {'Running' if runningState==0xFF else 'Stopped'}")
                tension = (regs[0] << 16) | regs[1]
                step    = (regs[2] << 16) | regs[3]
                
                return tension, step
        except ModbusException as e:
            print(f"[Node2] Get Status failed: {e}")
            self.node2Connected = False
        return None
        
    def get_aqua_data(self):
        # read input registers from 20, all 21 sensors, convert to 32-bit float
        try:
            result = self.client.read_input_registers(20, count=42, device_id=self.node2_addr)
            if result.isError():
                print("[Node2] Get Aqua Data failed")
                self.node2Connected = False
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
                print(f"[Node2] Aqua Data: {aqua_data}")
                return aqua_data
        except ModbusException as e:
            print(f"[Node2] Get Aqua Data failed: {e}")
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

if __name__ == "__main__":
    master = RS485Master(port="/dev/ttyUSB0")
    try:
        master.testMotorManuver()
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        master.close()

