import serial
import time

command1 = ['01', '03', '15', 'EB', '00', '07', '70', '30'] # 氯化物（Cl-）
command2 = ['01', '03', '15', 'F2', '00', '07', 'A1', 'F7'] # 濁度
command3 = ['01', '03', '16', '1C', '00', '07', 'C1', '86'] # 總懸浮固體

Actual_Conductivity = ['01', '03', '15', '82', '00', '07', 'A0', '2C']

ser = serial.Serial(port = "/dev/ttyUSB0", baudrate = 19200, bytesize = 8, parity = 'E', stopbits = 1, timeout = 10)
print(f"Request:{Actual_Conductivity}")
t1 = time.time()
command = bytes([int(x, 16) for x in Actual_Conductivity]) # commnad: list to bytes
ser.write(command) # write command to device
response = ser.read(19) # read response from device
response = [format(x, '02x') for x in response] # convert to hex
t2 = time.time()
print(t2 - t1 )
print(f"response:{response}")