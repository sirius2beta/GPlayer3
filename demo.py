import GPlayer
import DeviceManager

import MavManager

#mavrouter = MavManager.MavManager(None)
#mavrouter.connectVehicle("/dev/PD0")
#mavrouter.connectGCS('udp:192.168.0.99:14450',True)
#mavrouter.connectGCS('udp:100.117.209.85:14550',False)

gplayer = GPlayer.GPlayer()
gplayer.startLoop()
