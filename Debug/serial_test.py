import serial
import time

temp = ['01', '03', '15', '4A', '00', '07', '21', 'D2'] # 0:溫度 o
level_serface_elevation =['01', '03', '15', '66', '00', '07', 'E0', '1B'] # 表面高程 o
actual_conductivity = ['01', '03', '15', '82', '00', '07', 'A0', '2C'] # 5:實際導電率 o
ph = ['01', '03', '15', 'BA', '00', '07', '21', 'E1'] # pH值 o
orp = ['01', '03', '15', 'C8', '00', '07', '81', 'FA'] # 氧化還原電位（ORP）o
do_sat = ['01', '03', '15', 'D6', '00', '07', 'E1', 'FC'] # 溶解氧飽和度百分比 o
turbidity = ['01', '03', '15', 'F2', '00', '07', 'A1', 'F7'] # 濁度 o

ser = serial.Serial(port = "/dev/ttyUSB1", baudrate = 19200, bytesize = 8, parity = 'E', stopbits = 1, timeout = 10)
print(f"Request:{turbidity}")
t1 = time.time()
command = bytes([int(x, 16) for x in turbidity]) # commnad: list to bytes
ser.write(command) # write command to device
response = ser.read(19) # read response from device
response = [format(x, '02x') for x in response] # convert to hex
t2 = time.time()
print(f"response:{response}")

print(t2 - t1)