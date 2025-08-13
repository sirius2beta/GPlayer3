#!/bin/bash
VID=1209
PID=5740

# 找 Bus/Device 編號
BUSDEV=$(lsusb | grep "$VID:$PID" | head -n1 | awk '{print $2,$4}' | sed 's/://')
if [ -z "$BUSDEV" ]; then
  echo "❌ 找不到裝置 $VID:$PID"
  exit 1
fi
BUS=$(echo $BUSDEV | awk '{print $1}')
DEV=$(echo $BUSDEV | awk '{print $2}')

# 找對應的 sysfs 物理裝置路徑 (頂層節點)
SYS_PATH=$(udevadm info -q path -n /dev/bus/usb/$BUS/$DEV | sed -E 's|.*/usb([0-9\-\.]+)|\1|')
if [ -z "$SYS_PATH" ]; then
  echo "❌ 找不到物理裝置路徑"
  exit 1
fi
echo "📍 找到物理裝置路徑：$SYS_PATH"

# 找該設備底下的所有 ttyACM 裝置
TTY_LIST=$(find /sys/bus/usb/devices/$SYS_PATH* -name "ttyACM*" -exec basename {} \; 2>/dev/null)

# 如果找到 ttyACM 裝置，殺掉使用中的程序
if [ -n "$TTY_LIST" ]; then
  for tty in $TTY_LIST; do
    echo "🔍 檢查並強制關閉 /dev/$tty"
    sudo fuser -k /dev/$tty 2>/dev/null || true
  done
else
  echo "⚠ 沒有找到任何 ttyACM 裝置"
fi

# 重新掛載裝置（軟拔插）
echo "🔌 Unbind $SYS_PATH"
echo -n "$SYS_PATH" | sudo tee /sys/bus/usb/drivers/usb/unbind > /dev/null
sleep 1
echo "🔌 Bind $SYS_PATH"
echo -n "$SYS_PATH" | sudo tee /sys/bus/usb/drivers/usb/bind > /dev/null

sleep 1

# 顯示最新的 ttyACM 裝置訊息
echo "📢 重新掛載完成，最新 ttyACM 裝置："
ls /dev/ttyACM* 2>/dev/null || echo "無 ttyACM 裝置"
