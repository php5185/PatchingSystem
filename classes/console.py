class Console:
    @staticmethod
    def customPrint(targetFile, message):
        # If any of you want to test this, remember that the tail command won't work on windows.
        im_using_windows = False

        if (im_using_windows):
            print(message)
        else:
            with open("./logs/" + targetFile, 'w') as f:
                f.write(message + "\n")
