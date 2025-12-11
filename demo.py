import datetime
import warnings
import logging
import sys
import os
import time
import re
import logging
from datetime import datetime
from GToolBox import GToolBox

os.environ["GST_DEBUG"] = "0" # set GStreamer debug level

log_folder_path = "../GPlayerLog/debug"   # Changed to a subfolder for better organization
log_directory = os.path.expanduser(log_folder_path)       # 設定log存放路徑
if(not os.path.exists(log_directory)):                         # 如果路徑不存在，則建立
    os.makedirs(log_directory)                                 # 建立路徑

# 找出所有 log_xxxxxxxx.csv 檔案
existing_files = [f for f in os.listdir(log_directory) if f.startswith("log_") and f.endswith(".txt")]

# 從檔名抓出數字部分
indices = []
for f in existing_files:
    match = re.search(r"log_(\d+)\.txt", f)
    if match:
        indices.append(int(match.group(1)))

# 取最大值 + 1，如果沒有檔案就從 1 開始
file_index = max(indices) + 1 if indices else 1

# 檔名格式：log_00000001.txt
file_name = f"log_{file_index:08d}.txt"


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




if __name__ == '__main__':

    warnings.filterwarnings("ignore", category=UserWarning, module="numpy")

    toolBox = GToolBox(0) # initiate all modules
    try:
        while True:
            time.sleep(1)
    except Exception as e:
        logging.error(f"{e}")
        pass
    except KeyboardInterrupt:
        print("Exiting...")
