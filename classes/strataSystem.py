import time
import bcrypt
import os
from cryptography.fernet import Fernet
from console import Console

class StrataSystem:
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
        #send patch encrypted
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
