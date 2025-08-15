import datetime
import warnings
import concurrent.futures
import logging
import sys
import os
from datetime import datetime
from GToolBox import GToolBox


log_folder_path = "../GPlayerLog/output"  # Changed to a subfolder for better organization
log_directory = os.path.expanduser(log_folder_path)       # 設定log存放路徑
if(not os.path.exists(log_directory)):                         # 如果路徑不存在，則建立
    os.makedirs(log_directory)                                 # 建立路徑
current_time = datetime.now()                                       # 取得目前時間
file_name = f"log_{current_time.strftime('%Y%m%d_%H%M')}.txt"       # 設定檔案名稱
log_file = os.path.join(log_directory, file_name)         # 檔案路徑

# 建立 logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # 最低等級

# 檔案輸出
file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
file_handler.setLevel(logging.INFO)

# 終端機輸出
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 格式
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)
console_formatter = logging.Formatter(
    "%(message)s"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(console_formatter)

# 加入 handler
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def load_seagrass_detect():
    logging.info("SeagrassDetect importing...")
    t1 = datetime.datetime.now()
    from unet.SeagrassDetect import SeagrassDetect
    t2 = datetime.datetime.now()
    logging.info(f"SeagrassDetect imported in: {t2 - t1}")
    return SeagrassDetect(toolBox)

def load_jetson_detect():
    logging.info("JetsonDetect importing...")
    t1 = datetime.datetime.now()
    from JetsonDetect import JetsonDetect
    t2 = datetime.datetime.now()
    logging.info(f"JetsonDetect imported in: {t2 - t1}")
    return JetsonDetect(toolBox)

if __name__ == '__main__':

  warnings.filterwarnings("ignore", category=UserWarning, module="numpy")

  logging.info("GPlayer initialized successfully.")
  now = datetime.now()
  logging.info("*********************************")
  logging.info(f"Program started in: {now}")
  logging.info("*********************************")
   
  toolBox = GToolBox(0) # initiate all modules
  if toolBox.OS != "buster":
    logging.info("Starting SeagrassDetect and JetsonDetect in parallel...")

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
    
    toolBox.startLoop()
  input("Press Enter to exit...")  # Keep the program running until Enter is pressed
