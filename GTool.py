# Fundamental component of modules
class GTool:
    def __init__(self, toolbox):
        self._toolBox = toolbox 
    
    # toolbox can access all other modules
    def toolBox(self):
        return self._toolBox