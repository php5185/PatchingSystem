import random
import time

class iot:
    def __init__(self):
        self.lowMode = False

        self.getRawData()

    def activateLowMode(self):
        self.lowMode = True

    def sendData(self, data):
        # x=5
        print('Send Data:' + str(data))
        #sends data to node -- using Queue

    def getRawData(self):
        while(True):
            time.sleep(2)
            rowData = random.randrange(0, 10)

            if (self.lowMode):
                self.sendData(rowData)
            else:
                self.process(rowData)

    def patching(self, function):
        x=5

    # pylint: disable=E0202
    def process(self, data):
        # print('Im the core process')
        newData = data * -1
        print('Process:' + str(newData))

        self.sendData(newData)
        # print(data)

    def update(self, function='def newProcess(): print(\'Im the new core process\')'):
        context = {}
        exec(function, context)

        self.process = context['newProcess']

class node:
    def __init__(self, iotDevice):
        # self.iotDevice = iotDevice
        iotDevice.update()


    def processData(self):
        x=5

    def simulateIot(self):
        x=5

if __name__ == '__main__':
    device = iot()

    # TODO: Add Queues
    # device.update()

    # time.sleep(5)

    # print('here')
    # device.process()
