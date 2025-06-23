from scipy.spatial.transform import Rotation
import math
import numpy as np



def distance(K, R, h, u, v):
    uv = np.array([[u], [v], [1]])
    Pc = np.linalg.solve(K, uv)  # K 逆矩陣計算 Pc = np.matmul(np.linalg.inv(K), uv)
    Pw = R.T @ Pc  # 轉換到世界座標 Pw = np.matmul(np.linalg.inv(R), Pc)
    
    scale = h / Pw[-1]  # 讓 Z = 0
    Pw_ground = -Pw * scale  

    #dist = np.linalg.norm(Pw_ground[:2])  # 只考慮 X, Y 平面上的距離
    return Pw_ground

def getR0(pitch, roll):
    """
    計算相機的旋轉矩陣
    :param pitch: 俯仰角（與水平面的夾角，向上為正）
    :param roll: 翻滾角（與水平面的夾角，順時針為正）
    :return: 旋轉矩陣 (3x3)
    """
    # 先繞 X 軸旋轉 -90°，使得相機的初始 Z 軸對應世界 Y 軸
    R_base = Rotation.from_euler('x', -np.pi / 2, degrees=False).as_matrix()
    
    # 然後應用 Pitch（繞 X 軸）和 Roll（繞 Z 軸）
    R_pitch_roll = Rotation.from_euler('xz', [pitch, roll], degrees=False).as_matrix()
    
    # 總旋轉矩陣 = 基準旋轉 * Pitch-Roll 旋轉
    return R_base @ R_pitch_roll