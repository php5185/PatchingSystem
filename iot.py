import random
import time
from multiprocessing import Process, Queue
import bcrypt
import os
from cryptography.fernet import Fernet

class WeightSensor:
    def __init__(self, processWeightDataQueue, rawWeightDataQueue, iotStatusQueue):
        self.lowMode = False
        self.patchingProgress = 0
        self.processWeightDataQueue = processWeightDataQueue
        self.rawWeightDataQueue = rawWeightDataQueue
        self.iotStatusQueue = iotStatusQueue
        self.version = 'v1'
        self.p = None

    def listen_queue(self, queue):
        while True:
            time.sleep(2)
            if not queue.empty():
                patch = queue.get()
                if 'patch' in patch:
                    self.lowMode = True
                    self.iotStatusQueue.put({'lowMode': self.lowMode})
                    # self.p.stdin.write(str("hello").encode())
                    # self.p.stdin.flush()
                    patch_update = patch['patch']
                    #### decrypt patch
                    print("IN DECIVE PATCH RECEIVED: "+str(patch_update))
                    patch_decrypted = self.decrypt_message(patch_update)
                    print("IN DEVICE PATCH DECRYPTED: "+str(patch_decrypted))
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

        # print(decrypted_message.decode())
        return decrypted_message.decode()

    def sendProcessData(self, data):
        # x=5
        print('Send Process Data (' + self.version + '):' + str(data))
        self.processWeightDataQueue.put({'data': data})
        #sends data to node -- using Queue

    def sendRawData(self, data):
        # x=5
        print('Send Raw Data:' + str(data))
        self.rawWeightDataQueue.put({'data': data})
        #sends data to node -- using Queue

    def patch_progress(self):
        self.patchingProgress += 10
        if self.patchingProgress == 100:
            self.lowMode = False
            self.iotStatusQueue.put({'lowMode': self.lowMode })
            self.patchingProgress = 0
            self.version = 'v2'

    def getRawData(self):
        rawData = random.randrange(3000, 4000)
        if self.lowMode:
            self.patch_progress()
            print('iot in low mode')
            self.sendRawData(rawData)
        else:
            print('iot in regular mode')
            self.process(rawData)

    # pylint: disable=E0202
    def process(self, data):
        # print('Im the core process')
        newData = data / 1000
        print('Process:' + str(newData) + " kg")
        self.sendProcessData(newData)
        # print(data)

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
                    print('PLC PROCESS: ', data)
                    self.processData(data)
            self.send_over_communication_network()

    def processData(self, data):
        self.weightSensor.process(data)

    def send_over_communication_network(self):
        if not self.processWeightDataQueue.empty():
            process_data = self.processWeightDataQueue.get()
            if 'data' in process_data:
                print('PLC receives: ' + str(process_data['data']))
                self.communicationNetwork.put({'data': process_data['data']})
    # def simulateIot(self):
    #     x=5

class strataSystem:
    def __init__(self, patchQueue,communicationNetwork):
        self.patchQueue = patchQueue
        self.communicationNetwork = communicationNetwork

    def listen_process_queue(self):
        while True:
            time.sleep(1)
            if not self.communicationNetwork.empty():
                process_data = self.communicationNetwork.get()
                if 'data' in process_data:
                    print('System receives: ' + str(process_data['data']))

    def send_patch(self, patch):
        time.sleep(5)
        proceed = self.confirm_patch()
        # proceed = True
        #send patch encrypted
        self.generate_key()
        patch_encrypted = self.encrypt_message(patch)
        print("#############Patch encrypted: "+ str(patch_encrypted))
        if proceed:
            print('sending patch')
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
            print("works")
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
    patching_system.send_patch('def process(self,data):\n\tprint("Process:"+str(data/454)+" lbs")\n\tself.sendProcessData(data/454)')
    device_process.join()
    node_process.join()
    system_process.join()

#check to see if the patch succeeds, if not rollback
#check integrity of patch
