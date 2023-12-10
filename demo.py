import GPlayer
import DeviceManager
import MavManager
import datetime
from multiprocessing import Process


if __name__ == '__main__':

  
  now = datetime.datetime.now()
  print("*********************************")
  print("*********************************")
  print(f"Program started in: {now}")
  gplayer = GPlayer.GPlayer()
  gplayer.startLoop()
