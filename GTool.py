# 每個模組都要繼承GTool
class GTool:
    def __init__(self, toolbox):
        self._toolBox = toolbox #讓所有的模組可以取用其他模組的資源