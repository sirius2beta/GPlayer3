import GPlayer
import DeviceManager

gplayer = GPlayer.GPlayer()
#gplayer.on_setDevice = sm.setDevice
#sm.on_message = gplayer.sendMsg
gplayer.startLoop()
