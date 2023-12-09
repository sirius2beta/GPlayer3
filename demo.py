import GPlayer
import DeviceManager

if __name__ == '__main__':
  gplayer = GPlayer.GPlayer()
  #gplayer.on_setDevice = sm.setDevice
  #sm.on_message = gplayer.sendMsg
  gplayer.startLoop()
