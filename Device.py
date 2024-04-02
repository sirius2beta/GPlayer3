class Device:
    def __init__(self, idVendor="", idProduct = "", devPath=""):
        self.idProduct = idProduct
        self.idVendor = idVendor
        self.devPath = devPath
        self.ID = -1
        self.isOpened = False

    def write(self, msg):
        pass

    def read(self):
        pass


