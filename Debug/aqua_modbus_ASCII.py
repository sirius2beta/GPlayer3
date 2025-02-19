#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import serial
import struct
import threading
from Dev.Device import Device  # 假設這是您專案內的 Device 基底類別

class AquaDevice(Device):
    def __init__(self, device_type, dev_path="", sensor_group_list=[], networkManager=None):
        super().__init__(device_type, dev_path, sensor_group_list, networkManager)
        
        # 使用 Modbus ASCII 格式的喚醒命令
        # 原 RTU 命令為 ['01','0D','C1','E5']，僅取前兩個位元組 (01, 0D)
        # 0x01 + 0x0D = 14，LRC = 256 - 14 = 242 (0xF2)
        self.wake_up_command = ":010DF2\r\n"
        
        # 依據暫存器地址連續性，將 23 支感測器分成 5 組：
        # Group 1: Index 0～4  → 5 筆，讀取 5×7 = 35 registers, 起始地址 0x154A (5450)
        #   計算 LRC: 0x01+0x03+0x15+0x4A+0x00+0x23 = 0x86, LRC = 256 - 134 = 122 (0x7A)
        #   命令: ":0103154A00237A\r\n"
        #
        # Group 2: Index 5～10 → 6 筆，讀取 6×7 = 42 registers, 起始地址 0x1582 (5506)
        #   計算 LRC: 0x01+0x03+0x15+0x82+0x00+0x2A = 197, LRC = 256 - 197 = 59 (0x3B)
        #   命令: ":01031582002A3B\r\n"
        #
        # Group 3: Index 11～16 → 6 筆，讀取 6×7 = 42 registers, 起始地址 0x15B3 (5555)
        #   計算 LRC: 0x01+0x03+0x15+0xB3+0x00+0x2A = 246, LRC = 256 - 246 = 10 (0x0A)
        #   命令: ":010315B3002A0A\r\n"
        #
        # Group 4: Index 17～18 → 2 筆，讀取 2×7 = 14 registers, 起始地址 0x15EB (5611)
        #   計算 LRC: 0x01+0x03+0x15+0xEB+0x00+0x0E = 274, 274 mod 256 = 18, LRC = 256 - 18 = 238 (0xEE)
        #   命令: ":010315EB000EEE\r\n"
        #
        # Group 5: Index 19～22 → 4 筆，讀取 4×7 = 28 registers, 起始地址 0x1615 (5653)
        #   計算 LRC: 0x01+0x03+0x16+0x15+0x00+0x1C = 75, LRC = 256 - 75 = 181 (0xB5)
        #   命令: ":01031615001CB5\r\n"
        self.group_commands = [
            (0, 5,  ":0103154A00237A\r\n"),   # Group 1: Index 0～4
            (5, 6,  ":01031582002A3B\r\n"),   # Group 2: Index 5～10
            (11, 6, ":010315B3002A0A\r\n"),   # Group 3: Index 11～16
            (17, 2, ":010315EB000EEE\r\n"),   # Group 4: Index 17～18
            (19, 4, ":01031615001CB5\r\n")    # Group 5: Index 19～22
        ]
        
        # 用於存放 23 支感測器讀取結果的數值
        self.data_list = [0.0] * 23
        
        # 建立 Serial 連線（根據實際環境設定 dev_path、baudrate、parity 等參數）
        self.ser = serial.Serial(
            port=self.dev_path,
            baudrate=19200,
            bytesize=8,
            parity='E',
            stopbits=1,
            timeout=1
        )
        
        # 啟動持續讀取感測器資料的背景執行緒
        threading.Thread(target=self.reader, daemon=True).start()
    
    def send_command(self, command_str):
        """
        傳送一個 Modbus ASCII 命令，並讀取回應。
        回應以 CRLF 結尾，去除起始冒號與結尾的 CRLF，然後每 2 個字元切割成一個 hex 字串。
        """
        self.ser.write(command_str.encode('ascii'))
        resp_line = self.ser.readline().decode('ascii').strip()
        if not resp_line.startswith(':'):
            print("Invalid response:", resp_line)
            return []
        # 去除起始冒號後，每 2 個字元切割成列表
        payload = resp_line[1:]
        hex_list = [payload[i:i+2] for i in range(0, len(payload), 2)]
        return hex_list

    def reader(self):
        """
        持續讀取感測器數據：
          1. 先發送喚醒命令，並等待暖機時間（例如 16 秒，依據原廠要求）
          2. 依序發送五組讀取命令，每組回應中包含該 group 內所有感測器資料，
             每筆感測器資料佔 7 registers (14 bytes)，但僅取前 4 bytes (前兩個暫存器)轉換成 float
          3. 解析後依據表中的 index 存入 data_list 中
        """
        try:
            # 發送喚醒命令
            print("Sending wake-up command...")
            self.ser.write(self.wake_up_command.encode('ascii'))
            print("Waiting for warm-up (3 seconds)...")
            time.sleep(3)
            
            while True:
                for group in self.group_commands:
                    sensor_index_start, sensor_count, cmd = group
                    resp = self.send_command(cmd)
                    if len(resp) < 4:
                        print("Response too short for command:", cmd)
                        continue
                    try:
                        byte_count = int(resp[2], 16)
                    except Exception as e:
                        print("Error parsing byte count:", e)
                        continue
                    # 每支感測器資料讀取 7 registers => 7*2 = 14 bytes
                    expected_data_bytes = sensor_count * 14
                    if byte_count != expected_data_bytes:
                        print(f"Warning: Byte count {byte_count} != Expected {expected_data_bytes} for command {cmd}")
                    # 資料區從索引 3 到倒數第二個 (最後一個為 LRC)
                    data_bytes = resp[3:-1]
                    if len(data_bytes) < expected_data_bytes:
                        print("Incomplete data in response for command:", cmd)
                        continue
                    # 將該 group 內每筆感測器資料依序解析，每筆資料 14 個 byte，其中取前 4 byte 轉換成 float
                    for i in range(sensor_count):
                        start = i * 14
                        sensor_hex = ''.join(data_bytes[start:start+4])
                        try:
                            value = struct.unpack('>f', bytes.fromhex(sensor_hex))[0]
                        except Exception as e:
                            print(f"Error parsing sensor at index {sensor_index_start + i}: {e}")
                            value = 0.0
                        self.data_list[sensor_index_start + i] = value
                # 可依需求在一整輪讀取後稍作延遲（此處設為 0.1 秒）
                time.sleep(0.1)
        except serial.SerialException:
            print("Serial Error... Trying to reconnect...")
        except Exception as e:
            print("Reader error:", e)
    
    def get_sensor_data(self):
        return self.data_list
    
    def _io_loop(self):
        """
        定時（例如每秒）更新 networkManager 與 sensor_group_list 中的數據。
        (此部分根據您的系統架構進行相應調整)
        """
        while True:
            time.sleep(1)
            for i in range(len(self.data_list)):
                self.sensor_group_list[1].get_sensor(i).data = self.data_list[i]
            self.networkManager.sendMsg(b'\x04', self.sensor_group_list[1].pack())

if __name__ == '__main__':
    # 請根據實際環境設定 dev_path、sensor_group_list 與 networkManager 參數
    aqua = AquaDevice(device_type=1, dev_path="/dev/ttyUSB0", sensor_group_list=[], networkManager=None)
    while True:
        print(aqua.get_sensor_data())
        time.sleep(1)
