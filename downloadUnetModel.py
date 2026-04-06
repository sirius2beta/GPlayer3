import os
import torch
from torch2trt import torch2trt
from unet.unet import Unet

# 節省空間
# sudo systemctl isolate multi-user.target
# sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# 查看空間運用
# watch -n 0.5 free -h

# best model
https://drive.google.com/file/d/13WE7yi_qX41LSE5gqqSUjUpBUGsTcZJu/view?usp=drive_link

def download_model(drive_url, model_path):
    """從 Google Drive 下載模型（支援 fuzzy 模式）"""
    try:
        import gdown
    except ImportError:
        raise ImportError("請先安裝 gdown： pip install gdown")

    print(f"從 Google Drive 下載模型：{drive_url}")
    gdown.download(url=drive_url, output=model_path, fuzzy=True, quiet=False)
    print(f"下載完成：{model_path}")

# === 使用者可修改的參數 ===
default_url = "https://drive.google.com/file/d/1Dzv4M0cbvdR3fDcTmsftP0RKNABLGxGN/view?usp=sharing"
model_dir = "unet/model"
model_filename = "seagrass_model_resnet50.pth"
model_path = os.path.join(model_dir, model_filename)

# === Step 1: 建立資料夾 ===
os.makedirs(model_dir, exist_ok=True)

# === Step 2: 檢查是否需要下載或更新模型 ===
if not os.path.exists(model_path):
    print("模型檔不存在，開始下載...")
    download_model(default_url, model_path)
else:
    user_input = input(f"模型檔已存在：{model_path}\n是否要下載新的模型？ (y/N): ").strip().lower()
    if user_input == "y":
        new_url = input("請輸入新的 Google Drive 下載網址：").strip()
        if new_url:
            download_model(new_url, model_path)
        else:
            print("未輸入新網址，使用原本模型。")
    else:
        print("使用現有模型。")

# === Step 3: 載入並轉換模型 ===
model = Unet(
    model_path=model_path,
    num_classes=2,
    backbone="resnet50",
    input_shape=[512, 512],
    mix_type=0,
    cuda=True
)

if isinstance(model.net, torch.nn.DataParallel):
    model.net = model.net.module

dummy_input = torch.randn(1, 3, 512, 512).cuda()
import gc

# 在轉換前執行
gc.collect()
torch.cuda.empty_cache()
print("轉換為 TensorRT 中，請稍候...")
model.net = torch2trt(model.net, [dummy_input], fp16_mode=True, max_workspace_size=1 << 28)
print("TensorRT 模型轉換完成")

save_path = os.path.join(model_dir, "seagrass_model_resnet50_trt.pth")
torch.save(model.net.state_dict(), save_path)
print(f"模型已儲存：{save_path}")
