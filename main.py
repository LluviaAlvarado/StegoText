#imports
import math

import numpy as np

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition
from PIL import Image
from random import *

from block import *

Window.size = (400, 600)
Builder.load_file('stego.kv')

class WritingScreen(Screen):
    def __init__(self, **kwargs):
        #image info for algorithm
        self.pixAdd = 0
        self.numB = 0
        self.w = 0
        self.h = 0
        self.error = False
        #images
        self.original = None
        self.stego = None
        #original image address
        self.address = None
        self.filename = None
        # widgets
        self.status = None
        self.message = None
        super(WritingScreen, self).__init__(**kwargs)

    def mainMenu(self):
        sm.current = 'Menu'

    def reduceLetters(self, msg, max):
        x = self.numB - int(len(msg.text))
        max.text = 'Remaining Letters: ' + str(x)

    #loading the rgb image
    def loadImage(self,  selection, msg, stat, max):
        self.status = stat
        self.message = msg
        self.address = str(selection[0])
        self.filename = self.address.split('\\')
        try:
            self.original = Image.open(self.address, 'r')
            if self.original.mode == 'RGB':
                msg.is_focusable = True
                self.status.text = "Image Loaded Successfully!"
                self.status.color = 0, 1, 0, 1
            else:
                self.status.color = 1, 0, 0, 1
                msg.is_focusable = False
                self.status.text = "This is not an RGB Image!"
        except:
            self.status.color = 1, 0, 0, 1
            self.status.text = "Error loading image!"
            msg.is_focusable = False
            return
        #dimentions of the image
        self.w, self.h = self.original.size
        #number of pixels for address
        x = 0
        while 2**x < self.w*self.h:
            x += 1
        self.pixAdd = math.ceil(x / 3)
        #number of bytes for data
        self.numB = int(self.w*self.h/(self.pixAdd+3))
        max.text = 'Remaining Letters: ' + str(self.numB)
        #limit entry
        msg.input_filter = lambda text, from_undo: text[:self.numB - len(msg.text)]

    #creating random address for blocks
    def randomBlock(self, used):
        space = 3 + self.pixAdd
        x = randint(0, self.w-space)
        y = randint(0, self.h-1)
        free = False
        while not free:
            i = 0
            for add in used:
                if (add[0]-space < x < add[0]+space) and add[1] == y:
                    i += 1
            if i != 0:
                x = randint(0, self.w-space)
                y = randint(0, self.h-1)
            else:
                free = True
        address = [x, y]
        used.append(address)
        return Block(address)

    #creating new pixels
    def createNew(self, blocks):
        self.error = False
        #getting new values for data and address
        originalPixels = np.array(self.original)
        for block in blocks:
            #get the binary for the char
            bitsM = bin(ord(block.data))[2:]
            bitsM = '00000000'[len(bitsM):] + bitsM
            bitsM = list(bitsM)
            #get the 3 pixels to insert data
            i = 0
            while i < 3:
                try:
                    pixel = originalPixels[block.address[1], block.address[0] + i]
                except:
                    self.error = True
                    return
                #getting rgb bits
                j = 0
                while j < 3:
                    if len(bitsM) != 0:
                        bits = '{0:08b}'.format(pixel[j])
                        bits = list(bits)
                        #if we need to change the LSB
                        if bits[7] != bitsM[0]:
                            bits[7] = bitsM[0]
                            newByte = ''.join(bits)
                            pixel[j] = int(newByte, 2)
                        del(bitsM[0])
                    j += 1
                i += 1
            #inserting the link address
            sp = (self.pixAdd*3) / 2
            x = int(sp)
            if block.link is not None:
                bitsx = bin(block.link[0])[2:]
            else:
                bitsx = '1'*x
            #adjusting to size of space
            sz = ''
            for i in range(0, x):
                sz += '0'
            bitsx = sz[len(bitsx):] + bitsx
            bitsx = list(bitsx)
            x = math.ceil(sp)
            if block.link is not None:
                bitsy = bin(block.link[1])[2:]
            else:
                bitsy = '1'*x
            # adjusting to size of space
            sz = ''
            for i in range(0, x):
                sz += '0'
            bitsy = sz[len(bitsy):] + bitsy
            bitsy = list(bitsy)
            united = bitsx+bitsy
            # get the n pixels to insert address
            i = 0
            while i < self.pixAdd:
                try:
                    pixel = originalPixels[block.address[1], block.address[0] + i + 3]
                except:
                    self.error = True
                    return
                # getting rgb bits
                j = 0
                while j < 3:
                    if len(united) != 0:
                        bits = '{0:08b}'.format(pixel[j])
                        bits = list(bits)
                        # if we need to change the LSB
                        if bits[7] != united[0]:
                            bits[7] = united[0]
                            newByte = ''.join(bits)
                            pixel[j] = int(newByte, 2)
                        del (united[0])
                    j += 1
                i += 1
        # creating new image
        self.stego = Image.fromarray(originalPixels, 'RGB')
        ext = self.filename[len(self.filename)-1].split('.')
        newName = ext[0]+"StegoText.png"
        add = self.address.replace(self.filename[len(self.filename)-1], newName)
        # saving image
        self.stego.save(add)
        # saving key
        name = ext[0] + ".sk"
        add = self.address.replace(self.filename[len(self.filename) - 1], name)
        file = open(add, "w+")
        s = str(self.key[0]) + "," + str(self.key[1])
        file.write(s)
        file.close()


    #writing the message
    def write(self, message):
        usedAddresses = []
        new = self.randomBlock(usedAddresses);
        new.data = message[0]
        del(message[0])
        self.key = new.address
        previous = new
        blocks = []
        for byte in message:
            new = self.randomBlock(usedAddresses)
            new.data = byte
            previous.link = new.address
            blocks.append(previous)
            previous = new
        previous.link = None
        blocks.append(previous)
        #creating new image
        self.createNew(blocks)

    def startWriting(self, msg, stat):
        self.message = msg
        self.status = stat
        if not msg.is_focusable:
            self.status.text = 'Choose a Valid Image...'
            self.status.color = 1, 0, 0, 1
        elif not all(ord(char) < 128 for char in self.message.text):
            self.status.text = 'Non ASCII characters!'
            self.status.color = 1, 0, 0, 1
        else:
            m = list(self.message.text)
            self.write(m)
            if not self.error:
                self.status.text = 'Message Successfully Written!'
                self.status.color = 0, 1, 0, 1
            else:
                self.status.text = 'Ups! something went wrong...'
                self.status.color = 0, 1, 0, 1

class ReadingScreen(Screen):

    def __init__(self, **kwargs):
        super(ReadingScreen, self).__init__(**kwargs)
        #info for algorithm
        self.w = 0
        self.h = 0
        self.pixAdd = 0
        self.numB = 0
        self.key = None
        self.error = False
        #image
        self.reading = None
        self.address = None
        #widgets
        self.status = None
        self.message = ""

    def mainMenu(self):
        sm.current = 'Menu'

    #loading the key
    def loadKey(self, selection, stat):
        self.status = stat
        k = open(str(selection[0]), "r")
        ext = str(selection[0]).split('.')
        if ext[len(ext)-1] != 'sk':
            self.status.color = 1, 0, 0, 1
            self.status.text = "Invalid Key!"
        else:
            self.key = k.read()
            self.key = self.key.split(',')
            #converting to int
            self.key[0] = int(self.key[0])
            self.key[1] = int(self.key[1])
            self.status.color = 0, 1, 0, 1
            self.status.text = "Valid Key"

    # loading the rgb image
    def loadImage(self, selection, stat):
        self.message = ""
        self.status = stat
        self.address = str(selection[0])
        try:
            self.reading = Image.open(self.address)
            if self.reading.mode == 'RGB':
                self.status.text = "Image Loaded Successfully!"
                self.status.color = 0, 1, 0, 1
            else:
                self.status.color = 1, 0, 0, 1
                self.status.text = "This is not an RGB Image!"
        except:
            self.status.color = 1, 0, 0, 1
            self.status.text = "Error loading image!"
            return
        # dimentions of the image
        self.w, self.h = self.reading.size
        # number of pixels for address
        x = 0
        while 2 ** x < self.w * self.h:
            x += 1
        self.pixAdd = math.ceil(x / 3)
        # number of bytes for data
        self.numB = int(self.w * self.h / (self.pixAdd + 3))

    # get block by address
    def getBlock(self, address):
        self.error = False
        # getting new values for data and address
        originalPixels = np.array(self.reading)
        # get the 3 pixels to insert data
        i = 0
        data = []
        while i < 3:
            try:
                pixel = originalPixels[address[1], address[0] + i]
            except:
                self.error = True
                return
            # getting rgb bits
            j = 0
            while j < 3:
                bits = '{0:08b}'.format(pixel[j])
                bits = list(bits)
                # getting the LSB
                data.append(bits[7])
                j += 1
            i += 1
        #deleting 9th bit
        del(data[8])
        block = Block(address)
        d = ''.join(data)
        block.data = chr(int(d, 2))
        self.message += block.data
        # getting the link
        united = []
        i = 0
        while i < self.pixAdd:
            try:
                pixel = originalPixels[block.address[1], block.address[0] + i + 3]
            except:
                self.error = True
                return
            # getting rgb bits
            j = 0
            while j < 3:
                bits = '{0:08b}'.format(pixel[j])
                bits = list(bits)
                # getting the LSB
                united.append(bits[7])
                j += 1
            i += 1
        #getting the x
        sp = (self.pixAdd*3) / 2
        # adjusting to size of space
        x = []
        j = int(sp)
        for i in range(0, j):
            x.append(united[i])
        y = []
        k = math.ceil(sp)
        for i in range(j, j+k):
            y.append(united[i])
        #getting int
        x = ''.join(x)
        x = int(x, 2)
        y = ''.join(y)
        y = int(y, 2)
        #if not last block
        if x != (2**int(sp)) - 1:
            block.link = [x, y]
        return block

    # reading a message
    def read(self, block):
        if not self.error:
            if block.link is None:
                return
            else:
                self.read(self.getBlock(block.link))

    #start to read image
    def startReading(self, msg, st):
        self.status = st
        if self.reading is None:
            self.status.color = 1, 0, 0, 1
            self.status.text = 'No Image Loaded!'
        elif self.key is None:
            self.status.color = 1, 0, 0, 1
            self.status.text = 'No Key Loaded!'
        else:
            self.message = ""
            self.error = False
            b = Block(self.key)
            b.link = self.key
            self.read(b)
            if self.message == "" or self.error:
                self.status.color = 1, 0, 0, 1
                self.status.text = 'Wrong Key or Image.'
            else:
                msg.text = self.message
                self.status.color = 0, 1, 0, 1
                self.status.text = 'Message Successfully Read!'

class Menu(Screen):

    def optionWrite(self):
        sm.current = 'Write Stego Text'
    
    def optionRead(self):
        sm.current = 'Read Stego Text'



#screen manager
sm = ScreenManager(transition=SwapTransition())
sm.add_widget(Menu(name='Menu'))
sm.add_widget(WritingScreen(name='Write Stego Text'))
sm.add_widget(ReadingScreen(name='Read Stego Text'))

class StegoApp(App):
    def build(self):
        return sm

if __name__ == '__main__':
    StegoApp().run()
