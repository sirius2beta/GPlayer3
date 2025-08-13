for dev in /dev/*; do
  if [[ -e "$dev" ]]; then
    info=$(udevadm info -a -n "$dev")
    if echo "$info" | grep -q 'ATTRS{idVendor}=="1209"' && \
       echo "$info" | grep -q 'ATTRS{idProduct}=="5740"'; then
      echo "✅ 裝置 $dev 對應到 1209:5740"
    fi
  fi
done