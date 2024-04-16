import xml.etree.cElementTree as ET
from SensorGroup import Sensor, SensorGroup

class Config:
    def __init__(self, toolBox):
        self.toolBox = toolBox
        self.videoFormatList = []
        self.sensor_group_list = []
        print("init config...")
        configUrl = 'res/config.xml'
        tree = ET.parse(configUrl)
        self.xmlroot = tree.getroot()
        self._parse_sensor_group()
        self._parse_video_format()

        
    
    def getVideoFormatIndex(self, width, height, fps):
        index = 0
        for format in self.videoFormatList:
            if width==format[0] and height==format[1] and fps==format[2]:
                return index
            else:
                index+=1
        return -1
    
    def getFormatInfo(self, index):
        #return width, height, fps
        return [self.videoFormatList[index][0], self.videoFormatList[index][1], self.videoFormatList[index][2]]

    def getDecoderIndex(self, decoder):
        if decoder == 'MJPG':
            return 0
        elif decoder == 'YUYV':
            return 1
        else:
            return -1
    def _parse_video_format(self):
        for element in self.xmlroot.findall(".//enum[@name='VIDEO_FORMAT']/entry"):
            print(element.get('name'))
            self.videoFormatList.append(element.get('name').split(" "))
    def _parse_sensor_group(self):
                
        for sensorgroup in self.xmlroot.findall(".//enum[@name='SENSOR']/sensorgroup"):
            
            sensor_group_name = sensorgroup.get('name')
            sensor_group_index = sensorgroup.get('value')
            sensor_group = SensorGroup(index = int(sensor_group_index), name = sensor_group_name)
            print(f"Sensor group: {sensor_group_name}, {sensor_group_index}")
            for sensor in sensorgroup.findall('sensor'):
                
                value = int(sensor.get('value'))
                name = sensor.get('name')
                dtype = sensor.get('type')
                s = Sensor(sensor_type = value, name = name, data_type = dtype)
                sensor_group.add_sensor(s)
                print(f"  -Sensor: {name}, {value}, {dtype}")
            self.sensor_group_list.append(sensor_group)


