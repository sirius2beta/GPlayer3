from GTool import GTool
import struct
SENSOR = b'\x04'

class IOTest(GTool):
    def __init__(self, toolBox):
        super().__init__(toolBox)
        self.results = [[0,40,40,40,40,1,1]]
    
    def send_test_Msg(self):
        #test data
        results = self.results
        if results[0][5] <15:
            results[0][5]+=1
            results[0][6]+=1
        else:
            results[0][5]=0
            results[0][6]=0
        data = struct.pack("<B", 1) #cmd id
        data += struct.pack("<B", int(0)) #video no
        for result in results:
            data += struct.pack("<B", result[0])
            data += struct.pack("<H", result[1])
            data += struct.pack("<H", result[2])
            data += struct.pack("<H", result[3])
            data += struct.pack("<H", result[4])
            data += struct.pack("<f", result[5])
            data += struct.pack("<f", result[6])
        self.toolBox().networkManager.sendMsg(b'\x06', data)
        print("send")
