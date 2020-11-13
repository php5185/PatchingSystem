import random
import time
from multiprocessing import Process, Queue
import bcrypt
import os
from cryptography.fernet import Fernet
import inspect
import textwrap

# TODOS:
# 1 - check to see if the patch succeeds, if not rollback
# 2 - check integrity of patch
# 3 - Put the patch in a separate place to control how to send it.
# 4 - Clean the code

class Console:
    @staticmethod
    def customPrint(targetFile, message):
        # If any of you want to test this, remember that the tail command won't work on windows.
        im_using_windows = True

        if (im_using_windows):
            print(message)
        else:
            with open("./logs/" + targetFile, 'w') as f:
                f.write(message + "\n")

class WeightSensor:
    def __init__(self, processWeightDataQueue, rawWeightDataQueue, iotStatusQueue):
        self.lowMode = False
        self.patchingProgress = 0
        self.processWeightDataQueue = processWeightDataQueue
        self.rawWeightDataQueue = rawWeightDataQueue
        self.iotStatusQueue = iotStatusQueue
        self.version = 'v1'
        self.logFile = 'WeightSensor.txt'
        self.oldVersion = ""

    def listen_queue(self, queue):
        while True:
            time.sleep(2)
            if not queue.empty():
                patch = queue.get()
                if 'patch' in patch:
                    self.lowMode = True
                    self.iotStatusQueue.put({'lowMode': self.lowMode})
                    patch_update = patch['patch']
                    #### decrypt patch
                    patch_decrypted = self.decrypt_message(patch_update)
                    self.oldVersion = inspect.getsource(self.process)
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
        self.processWeightDataQueue.put({'data': data})
        #sends data to PLC -- using Queue

    def sendRawData(self, data):
        # x=5
        print_message = 'Send Raw Data:' + str(data)
        Console.customPrint(self.logFile, print_message) 
        self.rawWeightDataQueue.put({'data': data})
        #sends data to node -- using Queue

    def patch_progress(self):
        self.patchingProgress += 10
        if self.patchingProgress == 100:
            successful = self.validate_patch()
            if successful:
                self.version = 'v2'
                Console.customPrint(self.logFile, "PATCH SUCCESSFUL") 
            else:
                Console.customPrint(self.logFile, "PATCH FAILED, ROLLING BACK") 
                context = {}
                exec(str(textwrap.dedent(self.oldVersion)), context)
                setattr(self.__class__, 'process', context['process'])
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

    def update(self, function):
            context = {}
            exec(function, context)
            setattr(self.__class__, 'process', context['process'])

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
                    Console.customPrint(self.logFile, 'PLC PROCESS RAW DATA:' + str(data))
                    self.processData(data)
            self.send_over_communication_network()

    def processData(self, data):
        self.weightSensor.process(data, 'PLC.txt')

    def send_over_communication_network(self):
        if not self.processWeightDataQueue.empty():
            process_data = self.processWeightDataQueue.get()
            if 'data' in process_data:
                Console.customPrint(self.logFile, 'PLC SENDS DATA TO SYSTEM: ' + str(process_data['data']))
                self.communicationNetwork.put({'data': process_data['data']})

class strataSystem:
    def __init__(self, patchQueue,communicationNetwork):
        self.patchQueue = patchQueue
        self.communicationNetwork = communicationNetwork
        self.logFile = 'System.txt'

    def listen_process_queue(self):
        while True:
            time.sleep(1)
            if not self.communicationNetwork.empty():
                process_data = self.communicationNetwork.get()
                if 'data' in process_data:
                    Console.customPrint(self.logFile, 'System receives: ' + str(process_data['data']))

    def send_patch(self, patch):
        time.sleep(5)
        proceed = self.confirm_patch()
        self.generate_key()
        patch_encrypted = self.encrypt_message(patch)
        if proceed:
            Console.customPrint(self.logFile, 'Sending Patch')
            self.patchQueue.put({'patch': patch_encrypted})

    def confirm_patch(self):
        result = input('There is a new patch, would you like to install it? (y/n)')
        if result == "y":
            username = input("Please enter your username: ")
            password = input("Please enter your password: ")

            return self.authenticate(username, password)

    def authenticate(self, username, password):
        if bcrypt.hashpw(password.encode('utf-8'), os.environ['pass'].encode('utf-8')) == os.environ['pass'].encode(
                'utf-8') and username == os.environ['user']:
            return True
        else:
            print("It does not match")

    def generate_key(self):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

    def load_key(self):
        """
        Load the previously generated key
        """
        return open("secret.key", "rb").read()

    def encrypt_message(self, message):
        """
        Encrypts a message
        """
        key = self.load_key()
        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)

        print(encrypted_message)
        return encrypted_message

if __name__ == '__main__':
    rawWeightDataQueue = Queue()
    processWeightDataQueue = Queue()
    iotStatusQueue = Queue()
    patchQueue = Queue()
    communicationNetwork = Queue()

    patching_system = strataSystem(patchQueue, communicationNetwork)
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
