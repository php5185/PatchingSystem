import random
import time
from multiprocessing import Process, Queue
import bcrypt
import os
from cryptography.fernet import Fernet
from console import Console
from strataSystem import StrataSystem
from PLC import PLC
from weightSensor import WeightSensor

# TODOS:
# 3 - Put the patch in a separate place to control how to send it.
# 4 - Clean the code

if __name__ == '__main__':
    rawWeightDataQueue = Queue()
    processWeightDataQueue = Queue()
    iotStatusQueue = Queue()
    patchQueue = Queue()
    communicationNetwork = Queue()

    patching_system = StrataSystem(patchQueue, communicationNetwork)
    device = WeightSensor(processWeightDataQueue, rawWeightDataQueue, iotStatusQueue)
    plc = PLC(processWeightDataQueue, rawWeightDataQueue, iotStatusQueue, device, communicationNetwork)
    system_process = Process(target=patching_system.listen_process_queue, args=())
    system_process.start()
    device_process = Process(target=device.listen_queue, args=(patchQueue,))
    device_process.start()
    node_process = Process(target=plc.listen_data_queue, args=())
    node_process.start()
    patching_system.send_patch('def process(self, data, targetFile = None):\n\tself.weight_sensor_print("Process:"+str(data/454)+" lbs", targetFile)\n\tif targetFile != "Testing.txt":\n\t\tself.sendProcessData(data/454)')
    device_process.join()
    node_process.join()
    system_process.join()
