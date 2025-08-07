import torch
from torch2trt import torch2trt
from unet import Unet

model = Unet(
    model_path = "model/seagrass_model_resnet50.pth",
    num_classes = 2,
    backbone = "resnet50",
    input_shape = [512, 512],
    mix_type = 0,
    cuda = True
)

if isinstance(model.net, torch.nn.DataParallel):
    model.net = model.net.module

dummy_input = torch.randn(1, 3, 512, 512).cuda()

print("轉換為 TensorRT 中，請稍候...")
model.net = torch2trt(model.net, [dummy_input], fp16_mode=True)
print("TensorRT 模型轉換完成")

save_path = r"model/seagrass_model_resnet50_trt.pth"
torch.save(model.net.state_dict(), save_path)
print(f"模型已儲存：{save_path}")
