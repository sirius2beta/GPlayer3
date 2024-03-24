import xml.etree.cElementTree as ET

class Config:
    def __init__(self, toolBox):
        self.toolBox = toolBox
        self.videoFormatList = []
        print("init config...")
        configUrl = 'res/config.xml'
        tree = ET.parse(configUrl)
        root = tree.getroot()

        for element in root.findall(".//enum[@name='VIDEO_FORMAT']/entry"):
            print(element.get('name'))
            self.videoFormatList.append(element.get('name').split(" "))
    
    def getVideoFormatIndex(self, width, height, fps):
        index = 0
        for format in self.videoFormatList:
            if width==format[0] and height==format[1] and fps==format[2]:
                return index
            else:
                index+=1
        return -1

    def getDecoderIndex(self, decoder):
        if decoder == 'MJPG':
            return 0
        elif decoder == 'YUYV':
            return 1
        else:
            return -1




