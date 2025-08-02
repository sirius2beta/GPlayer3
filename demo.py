import datetime
from GToolBox import GToolBox

if __name__ == '__main__':
  try:
    from JetsonDetect import JetsonDetect
    
  except ImportError:
    print("Failed to import JetsonDetect.")
  print("GPlayer initialized successfully.")
  now = datetime.datetime.now()
  print("*********************************")
  print(f"Program started in: {now}")
  print("*********************************")
   
  toolBox = GToolBox(0) # initiate all modules
  jetsonDetect = JetsonDetect(toolBox) # initiate JetsonDetect
  toolBox.jetsonDetect = jetsonDetect # add to toolbox
  if toolBox.OS != "buster":
    jetsonDetect.startLoop() # start the JetsonDetect loop
  input("Press Enter to exit...")  # Keep the program running until Enter is pressed
