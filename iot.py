import random
import time
from multiprocessing import Process, Queue

class iot:
    def __init__(self, iotProcessDataQueue, iotRawDataQueue, iotStatusQueue):
        self.lowMode = False
        self.patchingProgress = 0
        self.iotProcessDataQueue = iotProcessDataQueue
        self.iotRawDataQueue = iotRawDataQueue
        self.iotStatusQueue = iotStatusQueue
        self.version = 'v1'

    def listen_queue(self, queue):
        while True:
            time.sleep(2)
            if not queue.empty():
                patch = queue.get()
                if 'patch' in patch:
                    self.lowMode = True
                    self.iotStatusQueue.put({'lowMode': self.lowMode })
                    print('set low mode to ' + str(self.lowMode))
                    patch_update = patch['patch']
                    self.update(patch_update)
                else:
                    self.getRawData()
            else:
                self.getRawData()

    def activateLowMode(self):
        self.lowMode = True

    def sendProcessData(self, data):
        # x=5
        print('Send Process Data (' + self.version + '):' + str(data))
        self.iotProcessDataQueue.put({'data': data})
        #sends data to node -- using Queue

    def sendRawData(self, data):
        # x=5
        print('Send Raw Data:' + str(data))
        self.iotRawDataQueue.put({'data': data})
        #sends data to node -- using Queue

    def patch_progress(self):
        self.patchingProgress += 10
        if self.patchingProgress == 100:
            self.lowMode = False
            self.iotStatusQueue.put({'lowMode': self.lowMode })
            self.patchingProgress = 0
            self.version = 'v2'

    def getRawData(self):
        rawData = random.randrange(0, 10)
        if self.lowMode:
            self.patch_progress()
            print('iot in low mode')
            self.sendRawData(rawData)
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
        self.sendProcessData(newData)
        # print(data)

    def update(self, function):
        context = {}
        exec(function, context)
        setattr(self.__class__, 'process', context['process'])

class node:
    def __init__(self, iotRawDataQueue, iotStatusQueue, iotDevice):
        self.iotRawDataQueue = iotRawDataQueue
        self.iotStatusQueue = iotStatusQueue
        self.lowMode = False
        self.iotDevice = iotDevice

    def listen_data_queue(self):
        while True:
            time.sleep(1)
            if not self.iotStatusQueue.empty():
                mode = self.iotStatusQueue.get()
                if 'lowMode' in mode:
                    self.lowMode = mode['lowMode']

            if self.lowMode:
                if not self.iotRawDataQueue.empty():
                    data = self.iotRawDataQueue.get()['data']
                    print('NODE PROCESS: ', data)
                    self.processData(data)

    def processData(self, data):
        self.iotDevice.process(data)

    def simulateIot(self):
        x=5

class system:
    def __init__(self, patchQueue,iotProcessDataQueue):
        self.patchQueue = patchQueue
        self.iotProcessDataQueue = iotProcessDataQueue

    def listen_process_queue(self):
        while True:
            time.sleep(1)
            if not self.iotProcessDataQueue.empty():
                process_data = self.iotProcessDataQueue.get()
                if 'data' in process_data:
                    print('System receives: ' + str(process_data['data']))

    def send_patch(self, patch):
        time.sleep(5)
        print('sending patch')
        self.patchQueue.put({'patch': patch})


if __name__ == '__main__':
    iotRawDataQueue = Queue()
    iotProcessDataQueue = Queue()
    iotStatusQueue = Queue()
    patchQueue = Queue()

    patching_system = system(patchQueue, iotProcessDataQueue)
    device = iot(iotProcessDataQueue, iotRawDataQueue, iotStatusQueue)
    nodeDevice = node(iotRawDataQueue, iotStatusQueue, device)
    system_process = Process(target=patching_system.listen_process_queue, args=())
    system_process.start()
    iot_process = Process(target=device.listen_queue, args=(patchQueue,))
    iot_process.start()
    node_process = Process(target=nodeDevice.listen_data_queue, args=())
    node_process.start()
    patching_system.send_patch('def process(self,data):\n\tself.sendProcessData(data-100)')
    iot_process.join()
    node_process.join()
    system_process.join()
