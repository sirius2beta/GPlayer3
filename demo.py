import datetime
from GToolBox import GToolBox

if __name__ == '__main__':

  print("GPlayer initialized successfully.")
  now = datetime.datetime.now()
  print("*********************************")
  print(f"Program started in: {now}")
  print("*********************************")
   
  toolBox = GToolBox(0) # initiate all modules
  if toolBox.OS != "buster":
    print("SeagrassDetect importing...")
    from unet.SeagrassDetect import SeagrassDetect
    print("JetsonDetect importing...")
    from JetsonDetect import JetsonDetect
    print("SeagrassDetect starting...")
    jetsonDetect = JetsonDetect(toolBox) # initiate JetsonDetect
    print("JetsonDetect starting...")
    seagrassDetect = SeagrassDetect(toolBox)

    toolBox.seagrassDetect = seagrassDetect # add to toolbox
    toolBox.jetsonDetect = jetsonDetect # add to toolbox

    jetsonDetect.startLoop() # start the JetsonDetect loop
    seagrassDetect.startLoop() # start the SeagrassDetect loop
    
  input("Press Enter to exit...")  # Keep the program running until Enter is pressed
