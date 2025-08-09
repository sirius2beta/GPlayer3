import datetime
import warnings
import concurrent.futures

from GToolBox import GToolBox

def load_seagrass_detect():
    print("SeagrassDetect importing...")
    t1 = datetime.datetime.now()
    from unet.SeagrassDetect import SeagrassDetect
    t2 = datetime.datetime.now()
    print(f"SeagrassDetect imported in: {t2 - t1}")
    return SeagrassDetect(toolBox)

def load_jetson_detect():
    print("JetsonDetect importing...")
    t1 = datetime.datetime.now()
    from JetsonDetect import JetsonDetect
    t2 = datetime.datetime.now()
    print(f"JetsonDetect imported in: {t2 - t1}")
    return JetsonDetect(toolBox)

if __name__ == '__main__':

  warnings.filterwarnings("ignore", category=UserWarning, module="numpy")

  print("GPlayer initialized successfully.")
  now = datetime.datetime.now()
  print("*********************************")
  print(f"Program started in: {now}")
  print("*********************************")
   
  toolBox = GToolBox(0) # initiate all modules
  if toolBox.OS != "buster":
    print("Starting SeagrassDetect and JetsonDetect in parallel...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 同时开始加载两个模块
        seagrass_future = executor.submit(load_seagrass_detect)
        jetson_future = executor.submit(load_jetson_detect)

        # 等待并获取返回值
        seagrassDetect = seagrass_future.result()
        jetsonDetect = jetson_future.result()
    
    

    toolBox.seagrassDetect = seagrassDetect # add to toolbox
    toolBox.jetsonDetect = jetsonDetect # add to toolbox

    jetsonDetect.startLoop() # start the JetsonDetect loop
    seagrassDetect.startLoop() # start the SeagrassDetect loop
    
  input("Press Enter to exit...")  # Keep the program running until Enter is pressed
