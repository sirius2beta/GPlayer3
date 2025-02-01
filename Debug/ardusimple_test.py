import serial
import time

# 設置串口參數
port = '/dev/ttyACM1'  # 替換為你的串口名稱，例如 '/dev/ttyUSB0' (Linux) 或 'COM3' (Windows)
baudrate = 115200  # 根據你的設備設置波特率

try:
    # 初始化串口
    ser = serial.Serial(port, baudrate, timeout=1)  # timeout 設置為 1 秒
    print(f"Connected to {port} at {baudrate} baud.")
    
    # 連續讀取數據
    while(True):
        if(ser.in_waiting > 0):  # 確保有數據可讀
            data = ser.readline().decode('utf-8').strip()  # 讀取一行並解碼
            print(f"Received: {data}")
            time.sleep(1)
except KeyboardInterrupt:
    # 當用戶手動中斷 (Ctrl+C) 時退出
    print("Stopped reading serial data.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if('ser' in locals() and ser.is_open):
        ser.close()
        print("Serial port closed.")
