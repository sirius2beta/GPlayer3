from config import Config

if __name__ == "__main__":
    print("ConfigReader test")
    cr = Config(None)
    sglist = cr.sensorGroupList
    sglist[1].get_sensor(1).data = 1.23
    sglist[0].get_sensor(1).data = 1.0
    data = sglist[1].pack()
    print(f"data: {data}")