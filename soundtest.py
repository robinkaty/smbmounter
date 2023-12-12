import platform
def beephappy():
    if platform.system() == 'Windows':
        import winsound
        winsound.Beep(1000, 500)
    elif platform.system() == 'Darwin':
        import os
        os.system('afplay /System/Library/Sounds/Tink.aiff')
    elif platform.system() == 'Linux':
        import os
        os.system('beep')


def beepsad():
    if platform.system() == 'Windows':
        import winsound
        winsound.Beep(500, 500)
    elif platform.system() == 'Darwin':
        import os
        os.system('afplay /System/Library/Sounds/Basso.aiff')
    elif platform.system() == 'Linux':
        import os
        os.system('beep')
        os.system('beep')

if __name__ == "__main__":
    beephappy()
    beepsad()
