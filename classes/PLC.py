import time
import os
from cryptography.fernet import Fernet
from console import Console

class PLC:
    def __init__(self, processWeightDataQueue, rawWeightDataQueue, iotStatusQueue, weightSensor, communicationNetwork):
        self.processWeightDataQueue = processWeightDataQueue
        self.rawWeightDataQueue = rawWeightDataQueue
        self.iotStatusQueue = iotStatusQueue
        self.lowMode = False
        self.weightSensor = weightSensor
        self.communicationNetwork = communicationNetwork
        self.logFile = 'PLC.txt'

    def listen_data_queue(self):
        while True:
            time.sleep(1)
            if not self.iotStatusQueue.empty():
                mode = self.iotStatusQueue.get()
                if 'lowMode' in mode:
                    self.lowMode = mode['lowMode']

            if self.lowMode:
                if not self.rawWeightDataQueue.empty():
                    data = self.rawWeightDataQueue.get()['data']
                    Console.customPrint(self.logFile, 'PLC PROCESS: ' + str(data))
                    self.processData(data)
            self.send_over_communication_network()

    def processData(self, data):
        self.weightSensor.process(data)

    def send_over_communication_network(self):
        if not self.processWeightDataQueue.empty():
            process_data = self.processWeightDataQueue.get()
            if 'data' in process_data:
                Console.customPrint(self.logFile, 'PLC receives: ' + str(process_data['data']))
                self.communicationNetwork.put({'data': process_data['data']})
