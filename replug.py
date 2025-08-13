#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import re

def get_usb_id(dev_path):
    try:
        # 取得 udev 資訊
        result = subprocess.check_output(['udevadm', 'info', '-q', 'path', '-n', dev_path], text=True).strip()
        # 範例：/devices/platform/.../1-2.3.3/1-2.3.3:1.0/tty/ttyACM0
        # 抓出最接近 root 的 USB ID（不含介面）
        match = re.search(r'(\d+-[\d\.]+)(?=/\d+-[\d\.]+:\d+\.\d+/tty/)', result)
        if match:
            return match.group(1)
        else:
            # 若沒 match，抓最後一個 1-2.x.x
            match = re.search(r'(\d+-[\d\.]+)', result)
            return match.group(1) if match else None
    except subprocess.CalledProcessError:
        return None

def replug_usb(usb_id):
    unbind_path = '/sys/bus/usb/drivers/usb/unbind'
    bind_path = '/sys/bus/usb/drivers/usb/bind'

    if not os.path.exists(unbind_path) or not os.path.exists(bind_path):
        print("❌ 找不到 bind/unbind 接口，請確認系統支援")
        return False

    try:
        print(f"🔌 拔除裝置 {usb_id} ...")
        subprocess.run(['sudo', 'tee', unbind_path], input=usb_id + '\n', text=True)
        time.sleep(1)
        print(f"🔌 插回裝置 {usb_id} ...")
        subprocess.run(['sudo', 'tee', bind_path], input=usb_id + '\n', text=True)
        return True
    except Exception as e:
        print(f"❌ 插拔失敗: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: sudo python3 usb_replug.py /dev/ttyACM0")
        sys.exit(1)

    dev_path = sys.argv[1]

    if not os.path.exists(dev_path):
        print(f"❌ 找不到裝置：{dev_path}")
        sys.exit(1)

    usb_id = get_usb_id(dev_path)
    if not usb_id:
        print(f"❌ 無法取得 USB ID，請確認 {dev_path} 是 USB 裝置")
        sys.exit(1)

    print(f"✅ 找到 USB ID：{usb_id}")
    success = replug_usb(usb_id)

    if success:
        print(f"✅ 已完成插拔操作，請稍候檢查 {dev_path}")
    else:
        print("❌ 插拔操作失敗")

if __name__ == '__main__':
    main()
