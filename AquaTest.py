import serial
import time

def setup_modbus_rtu():
    ser = serial.Serial(
        port='/dev/ttyUSB0',  # 根據你的設備調整端口
        baudrate=19200,       # 波特率
        bytesize=serial.EIGHTBITS,  # 數據位：8位
        parity=serial.PARITY_EVEN,  # 奇偶校驗：Even
        stopbits=serial.STOPBITS_ONE,  # 停止位：1位
        timeout=2  # 設置超時時間，根據需要調整
    )

    if ser.is_open:
        print("串口已打開，開始進行Modbus通訊...")
    else:
        print("無法打開串口")

    while(True):
        s = time.time()
        command = ['01', '03', '15', '4A', '00', '07', '21', 'D2']
        print(f"request:{command}")
        command = bytes([int(x, 16) for x in command]) # commnad: list to bytes
        ser.write(command) # write command to device
        response = ser.read(19) # read response from device
        response = [format(x, '02x') for x in response] # convert to hex
        print(f"response:{response}")
        e = time.time()
        print(f"s={s}, e={e}, t={e-s}")
        # time.sleep(0.1)

if __name__ == "__main__":
    setup_modbus_rtu()
