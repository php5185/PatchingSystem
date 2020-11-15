import random
import time
import bcrypt
import os
from cryptography.fernet import Fernet
from console import Console
import textwrap
import inspect

class WeightSensor:
    def __init__(self, processWeightDataQueue, rawWeightDataQueue, iotStatusQueue):
        self.lowMode = False
        self.patchingProgress = 0
        self.patchInProgress = False
        self.processWeightDataQueue = processWeightDataQueue
        self.rawWeightDataQueue = rawWeightDataQueue
        self.iotStatusQueue = iotStatusQueue
        self.version = 'v1'
        self.logFile = 'WeightSensor.txt'
        self.p = None
        self.oldVersion = ""
        self.initialPatchFailed = False

    def listen_queue(self, queue):
        while True:
            time.sleep(2)
            if not queue.empty():
                patch = queue.get()
                if 'patch' in patch:
                    self.lowMode = True
                    self.patchInProgress = True
                    self.iotStatusQueue.put({'lowMode': self.lowMode})
                    patch_update = patch['patch']
                    #### decrypt patch
                    patch_decrypted = self.decrypt_message(patch_update)
                    self.update(str(patch_decrypted))
                else:
                    self.getRawData()
            else:
                self.getRawData()

    def activateLowMode(self):
        self.lowMode = True

    def load_key(self):
        """
        Load the previously generated key
        """
        return open("secret.key", "rb").read()

    def decrypt_message(self, encrypted_message):
        """
        Decrypts an encrypted message
        """
        key = self.load_key()
        f = Fernet(key)
        decrypted_message = f.decrypt(encrypted_message)
        return decrypted_message.decode()

    def sendProcessData(self, data):
        print_message = 'Send Process Data (' + self.version + '):' + str(data)
        Console.customPrint(self.logFile, print_message)
        self.processWeightDataQueue.put({'data': data})
        #sends data to node -- using Queue

    def sendRawData(self, data):
        print_message = 'Send Raw Data:' + str(data)
        Console.customPrint(self.logFile, print_message)
        self.rawWeightDataQueue.put({'data': data})
        #sends data to node -- using Queue

    def patch_progress(self):
        self.patchingProgress += 10
        if self.patchingProgress == 100:
            if not self.initialPatchFailed:
                successful = self.validate_patch()
                if successful:
                    self.version = 'v2'
                    Console.customPrint(self.logFile, "PATCH SUCCESSFUL") 
                else:
                    Console.customPrint(self.logFile, "PATCH FAILED, ROLLING BACK")
                    self.rollback()
 
            else:
                Console.customPrint(self.logFile, "PATCH FAILED, ROLLING BACK")
            self.lowMode = False
            self.iotStatusQueue.put({'lowMode': self.lowMode })
            self.patchingProgress = 0

    def validate_patch(self):
        try:
            for i in range(0,10):
                testData = random.randrange(3000, 4000)
                self.process(testData, 'Testing.txt')
            return True
        except Exception as e:
            print(e)
            return False

    def getRawData(self):
        rawData = random.randrange(3000, 4000)
        if self.lowMode:
            self.patch_progress()
            Console.customPrint(self.logFile, 'iot in low mode')
            self.sendRawData(rawData)
        else:
            Console.customPrint(self.logFile, 'iot in regular mode')
            self.process(rawData)

    # pylint: disable=E0202
    def process(self, data, targetFile = None):
        newData = data / 1000
        self.weight_sensor_print('Process:' + str(newData) + " kg", targetFile)
        if targetFile != "Testing.txt":
            self.sendProcessData(newData)
    
    def weight_sensor_print(self, message, targetFile = None):
        if not targetFile:
            targetFile = self.logFile

        Console.customPrint(targetFile, message)

    def save_patch(self):
        self.oldVersion = inspect.getsource(self.process)

    def rollback(self):
        context = {}
        exec(str(textwrap.dedent(self.oldVersion)), context)
        setattr(self.__class__, 'process', context['process'])

    def update(self, function):
        self.save_patch()
        context = {}
        try:
            exec(function, context)
            setattr(self.__class__, 'process', context['process'])
        except:
            self.initialPatchFailed = True
