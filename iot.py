import random
import time
from multiprocessing import Process, Queue


class iot:
    def __init__(self):
        self.lowMode = False
        self.patchingProgress = 0
    def listen_queue(self, queue):
        while True:
            time.sleep(2)
            if not queue.empty():
                patch = queue.get()
                if 'patch' in patch:
                    self.lowMode = True
                    print('set low mode to ' + str(self.lowMode))
                    patch_update = patch['patch']
                    self.update(patch_update)
                else:
                    self.getRawData()
            else:
                self.getRawData()

    def activateLowMode(self):
        self.lowMode = True

    def sendData(self, data):
        # x=5
        print('Send Data:' + str(data))
        #sends data to node -- using Queue

    def patch_progress(self):
        self.patchingProgress += 10
        if self.patchingProgress == 100:
            self.lowMode = False
            self.patchingProgress = 0

    def getRawData(self):
        rawData = random.randrange(0, 10)
        if self.lowMode:
            self.patch_progress()
            print('iot in low mode')
            self.sendData(rawData)
        else:
            print('iot in regular mode')
            self.process(rawData)

    def patching(self, function):
        x=5

    # pylint: disable=E0202
    def process(self, data):
        # print('Im the core process')
        newData = data * -1
        print('Process:' + str(newData))

        self.sendData(newData)
        # print(data)

    def update(self, function):
        context = {}
        exec(function, context)
        setattr(self.__class__, 'process', context['process'])

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
    patchQueue = Queue()
    iot_process = Process(target=device.listen_queue, args=(patchQueue,))
    iot_process.start()
    time.sleep(4)
    patchQueue.put({'patch': 'def process(self,data):\n\tself.sendData(data-100)'})

    iot_process.join()


    # TODO: Add Queues
    # device.update()


    # print('here')
    # device.process()
