#!/usr/bin/python
#
# Created by Alan Aufderheide, February 2013
#
# This provides a menu driven application using the LCD Plates
# from Adafruit Electronics.
import array
import smbus
import socket
import fcntl
import struct
import commands
import os
from string import split
from time import sleep, strftime, localtime
from xml.dom.minidom import *
from Adafruit_I2C import Adafruit_I2C
from Adafruit_MCP230xx import Adafruit_MCP230XX
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from ListSelector import ListSelector
from wifi import Cell, Scheme
from ola.ClientWrapper import ClientWrapper

configfile = 'lcdmenu.xml'
# set DEBUG=1 for print debug statements
DEBUG = 0
DISPLAY_ROWS = 2
DISPLAY_COLS = 16
universe = 1

# set busnum param to the correct value for your pi
lcd = Adafruit_CharLCDPlate(busnum = 1)
# in case you add custom logic to lcd to check if it is connected (useful)
#if lcd.connected == 0:
#    quit()

lcd.begin(DISPLAY_COLS, DISPLAY_ROWS)
lcd.backlight(lcd.OFF)

# commands
def DmxSent(state):
  wrapper.Stop()

def ConvertAddrtoNum(addr):
    num = (addr[0]*100) + (addr[1] * 10) + addr[2]
    return num

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def updateDMXChan(startrow, startcol, addr):
    lcd.setCursor(startrow, startcol)
    lcd.message(str(addr[0])+str(addr[1])+str(addr[2]))
    lcd.setCursor(startrow+2, startcol)


def validateAddr(addr, change, curp):
    if curp > 2 or curp < 0:
        return addr
    if change == 1:
        addr[curp] += 1
        if addr[curp] > 9:
            addr=validateAddr(addr, change, curp-1)
            addr[curp]=0
    if change == -1:
        addr[curp] -= 1
        if addr[curp] < 0:
            addr=validateAddr(addr, change, curp-1)
            addr[curp]=9
    if addr[0] >= 5 and addr[1] >= 1 and addr [2] >= 2:
        addr = [0,0,0]
    if addr[0] > 5:
        addr = [5,1,2]
    if addr[0] >= 5 and addr[1] > 1:
        addr = [5,1,2]
    if addr[0] < 0 and addr[1] == 0 and addr[2] == 0:
        addr = [5,1,2]
    return addr
    
def AddrCheck():
    lcd.clear()
    addr = [0,0,1]
    firstaddrnum = -1
    curp = 2
    curc=10
    i=1
    lcd.message('Channel Check\n1st Addr:')
    updateDMXChan(curc, 1, addr)
    lcd.cursor()
    while 1:
        if lcd.buttonPressed(lcd.SELECT):
            if firstaddrnum != -1:
                lcd.clear()
                secondaddrnum=ConvertAddrtoNum(addr)
                if secondaddrnum < firstaddrnum:
                    lcd.clear()
                    lcd.message('ERROR: 1st Addr is\n> than 2nd Addr')
                    while 1:
                        if lcd.buttonPressed(lcd.SELECT):
                            break
                    break
                print(firstaddrnum, secondaddrnum)
                lcd.noCursor()
                #lcd.message('Testing Addr:\nUP=+1 DOWN=-1')
                lcd.message('Testing Addr:')
                for i in range(1,secondaddrnum+1):
                    data = array.array('B')
                    for i in range(1,firstaddrnum):
                        data.append(0)
                        i+=1
                    data.append(255)
                    print("Chan:"+str(i)+" "+"Frame:"+str(data))
                    lcd.setCursor(13,0)
                    lcd.message(i)
                    #while 1:
                    #    sleep(.15)
                    #    if lcd.buttonPressed(lcd.UP):
                    #        i+=1
                    #        firstaddrnum+=1
                    #        break
                    #    if lcd.buttonPressed(lcd.DOWN):
                    #        i-=1
                    #        firstaddrnum-=1
                    #        break
                    #    sleep(.15)
                    client.SendDmx(universe, data, DmxSent)
                    wrapper.Run()
                    i+=1
                    firstaddrnum+=1
                    sleep(1)
                    if i==secondaddrnum+1:
                        for i in range(1,secondaddrnum+2):
                            data = array.array('B')
                            data.append(0)
                            i+=1
                        client.SendDmx(universe, data, DmxSent)
                        wrapper.Run()
                        break
                break
            if firstaddrnum == -1:
                firstaddrnum = ConvertAddrtoNum(addr)
                lcd.clear()
                lcd.message('Channel Check\n2nd Addr:')
                updateDMXChan(curc, 1, addr)
                curc = 10
        if lcd.buttonPressed(lcd.UP):
            addr=validateAddr(addr, 1, curp)
            updateDMXChan(curc,1, addr)
        if lcd.buttonPressed(lcd.DOWN):
            addr=validateAddr(addr, -1, curp)
            updateDMXChan(curc,1, addr)
        if lcd.buttonPressed(lcd.LEFT):
            if curp != 0:
                curp -=1
        if lcd.buttonPressed(lcd.RIGHT):
            if curp != 2:
                curp +=1
        lcd.setCursor(curp+curc, 1)
        sleep(.15)

def DoQuit():
    lcd.clear()
    lcd.message('Are you sure?\nPress Sel for Y')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        if lcd.buttonPressed(lcd.SELECT):
            lcd.clear()
            lcd.backlight(lcd.OFF)
            quit()
        sleep(0.25)

def DoDebug():
    lcd.clear()
    lcd.message('Are you sure?\nPress Sel for Y')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        if lcd.buttonPressed(lcd.SELECT):
            lcd.clear()
            lcd.backlight(lcd.OFF)
            commands.getoutput("sudo /home/pi/debug.sh")
            quit()
        sleep(0.25)

def DoRestart():
    lcd.clear()
    lcd.message('Are you sure?\nPress Sel for Y')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        if lcd.buttonPressed(lcd.SELECT):
            lcd.clear()
            lcd.backlight(lcd.OFF)
            commands.getoutput("sudo /home/pi/start.sh")
            quit()
        sleep(0.25)

def DoShutdown():
    lcd.clear()
    lcd.message('Are you sure?\nPress Sel for Y')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        if lcd.buttonPressed(lcd.SELECT):
            lcd.clear()
            lcd.backlight(lcd.OFF)
            commands.getoutput("sudo shutdown -h now")
            quit()
        sleep(0.25)

def DoReboot():
    lcd.clear()
    lcd.message('Are you sure?\nPress Sel for Y')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        if lcd.buttonPressed(lcd.SELECT):
            lcd.clear()
            lcd.backlight(lcd.OFF)
            commands.getoutput("sudo reboot")
            quit()
        sleep(0.25)

def LcdOff():
    lcd.backlight(lcd.OFF)

def LcdOn():
    lcd.backlight(lcd.ON)

def LcdRed():
    lcd.backlight(lcd.RED)

def LcdGreen():
    lcd.backlight(lcd.GREEN)

def LcdBlue():
    lcd.backlight(lcd.BLUE)

def LcdYellow():
    lcd.backlight(lcd.YELLOW)

def LcdTeal():
    lcd.backlight(lcd.TEAL)

def LcdViolet():
    lcd.backlight(lcd.VIOLET)

def ShowDateTime():
    if DEBUG:
        print('in ShowDateTime')
    lcd.clear()
    while not(lcd.buttonPressed(lcd.LEFT)):
        sleep(0.25)
        lcd.home()
        lcd.message(strftime('%a %b %d %Y\n%I:%M:%S %p', localtime()))
    
def ValidateDateDigit(current, curval):
    # do validation/wrapping
    if current == 0: # Mm
        if curval < 1:
            curval = 12
        elif curval > 12:
            curval = 1
    elif current == 1: #Dd
        if curval < 1:
            curval = 31
        elif curval > 31:
            curval = 1
    elif current == 2: #Yy
        if curval < 1950:
            curval = 2050
        elif curval > 2050:
            curval = 1950
    elif current == 3: #Hh
        if curval < 0:
            curval = 23
        elif curval > 23:
            curval = 0
    elif current == 4: #Mm
        if curval < 0:
            curval = 59
        elif curval > 59:
            curval = 0
    elif current == 5: #Ss
        if curval < 0:
            curval = 59
        elif curval > 59:
            curval = 0
    return curval

def SetDateTime():
    if DEBUG:
        print('in SetDateTime')
    # M D Y H:M:S AM/PM
    curtime = localtime()
    month = curtime.tm_mon
    day = curtime.tm_mday
    year = curtime.tm_year
    hour = curtime.tm_hour
    minute = curtime.tm_min
    second = curtime.tm_sec
    ampm = 0
    if hour > 11:
        hour -= 12
        ampm = 1
    curr = [0,0,0,1,1,1]
    curc = [2,5,11,1,4,7]
    curvalues = [month, day, year, hour, minute, second]
    current = 0 # start with month, 0..14
    lcd.clear()
    lcd.message(strftime("%b %d, %Y  \n%I:%M:%S %p  ", curtime))
    lcd.blink()
    lcd.setCursor(curc[current], curr[current])
    sleep(0.5)
    while 1:
        curval = curvalues[current]
        if lcd.buttonPressed(lcd.UP):
            curval += 1
            curvalues[current] = ValidateDateDigit(current, curval)
            curtime = (curvalues[2], curvalues[0], curvalues[1], curvalues[3], curvalues[4], curvalues[5], 0, 0, 0)
            lcd.home()
            lcd.message(strftime("%b %d, %Y  \n%I:%M:%S %p  ", curtime))
            lcd.setCursor(curc[current], curr[current])
        if lcd.buttonPressed(lcd.DOWN):
            curval -= 1
            curvalues[current] = ValidateDateDigit(current, curval)
            curtime = (curvalues[2], curvalues[0], curvalues[1], curvalues[3], curvalues[4], curvalues[5], 0, 0, 0)
            lcd.home()
            lcd.message(strftime("%b %d, %Y  \n%I:%M:%S %p  ", curtime))
            lcd.setCursor(curc[current], curr[current])
        if lcd.buttonPressed(lcd.RIGHT):
            current += 1
            if current > 5:
                current = 5
            lcd.setCursor(curc[current], curr[current])
        if lcd.buttonPressed(lcd.LEFT):
            current -= 1
            if current < 0:
                lcd.noBlink()
                return
            lcd.setCursor(curc[current], curr[current])
        if lcd.buttonPressed(lcd.SELECT):
            # set the date time in the system
            lcd.noBlink()
            os.system(strftime('sudo date --set="%d %b %Y %H:%M:%S"', curtime))
            break
        sleep(0.25)

    lcd.noBlink()

def ShowIPAddress():
    if DEBUG:
        print('in ShowIPAddress')
    lcd.clear()
    disp = "IP Address :\n" + get_ip_address('wlan0')
    lcd.message(disp)
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)
    
def FadeAllAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

def FadeRangeAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

def FadeOneAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

def SetAllAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

def SetRangeAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

def SetOneAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

def RecieveAllAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

def RecieveRangeAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

def RecieveOneAddr():
    lcd.clear()
    lcd.message('Not Working\n... Yet :)')
    while 1:
        if lcd.buttonPressed(lcd.LEFT):
            break
        sleep(0.25)

class CommandToRun:
    def __init__(self, myName, theCommand):
        self.text = myName
        self.commandToRun = theCommand
    def Run(self):
        self.clist = split(commands.getoutput(self.commandToRun), '\n')
        if len(self.clist) > 0:
            lcd.clear()
            lcd.message(self.clist[0])
            for i in range(1, len(self.clist)):
                while 1:
                    if lcd.buttonPressed(lcd.DOWN):
                        break
                    sleep(0.25)
                lcd.clear()
                lcd.message(self.clist[i-1]+'\n'+self.clist[i])          
                sleep(0.5)
        while 1:
            if lcd.buttonPressed(lcd.LEFT):
                break

class Widget:
    def __init__(self, myName, myFunction):
        self.text = myName
        self.function = myFunction
        
class Folder:
    def __init__(self, myName, myParent):
        self.text = myName
        self.items = []
        self.parent = myParent

def HandleSettings(node):
    global lcd
    if node.getAttribute('lcdColor').lower() == 'red':
        lcd.backlight(lcd.RED)
    elif node.getAttribute('lcdColor').lower() == 'green':
        lcd.backlight(lcd.GREEN)
    elif node.getAttribute('lcdColor').lower() == 'blue':
        lcd.backlight(lcd.BLUE)
    elif node.getAttribute('lcdColor').lower() == 'yellow':
        lcd.backlight(lcd.YELLOW)
    elif node.getAttribute('lcdColor').lower() == 'teal':
        lcd.backlight(lcd.TEAL)
    elif node.getAttribute('lcdColor').lower() == 'violet':
        lcd.backlight(lcd.VIOLET)
    elif node.getAttribute('lcdColor').lower() == 'white':
        lcd.backlight(lcd.ON)
    if node.getAttribute('lcdBacklight').lower() == 'on':
        lcd.backlight(lcd.ON)
    elif node.getAttribute('lcdBacklight').lower() == 'off':
        lcd.backlight(lcd.OFF)

def ProcessNode(currentNode, currentItem):
    children = currentNode.childNodes

    for child in children:
        if isinstance(child, xml.dom.minidom.Element):
            if child.tagName == 'settings':
                HandleSettings(child)
            elif child.tagName == 'folder':
                thisFolder = Folder(child.getAttribute('text'), currentItem)
                currentItem.items.append(thisFolder)
                ProcessNode(child, thisFolder)
            elif child.tagName == 'widget':
                thisWidget = Widget(child.getAttribute('text'), child.getAttribute('function'))
                currentItem.items.append(thisWidget)
            elif child.tagName == 'run':
                thisCommand = CommandToRun(child.getAttribute('text'), child.firstChild.data)
                currentItem.items.append(thisCommand)

class Display:
    def __init__(self, folder):
        self.curFolder = folder
        self.curTopItem = 0
        self.curSelectedItem = 0
    def display(self):
        if self.curTopItem > len(self.curFolder.items) - DISPLAY_ROWS:
            self.curTopItem = len(self.curFolder.items) - DISPLAY_ROWS
        if self.curTopItem < 0:
            self.curTopItem = 0
        if DEBUG:
            print('------------------')
        str = ''
        for row in range(self.curTopItem, self.curTopItem+DISPLAY_ROWS):
            if row > self.curTopItem:
                str += '\n'
            if row < len(self.curFolder.items):
                if row == self.curSelectedItem:
                    cmd = '-'+self.curFolder.items[row].text
                    if len(cmd) < 16:
                        for row in range(len(cmd), 16):
                            cmd += ' '
                    if DEBUG:
                        print('|'+cmd+'|')
                    str += cmd
                else:
                    cmd = ' '+self.curFolder.items[row].text
                    if len(cmd) < 16:
                        for row in range(len(cmd), 16):
                            cmd += ' '
                    if DEBUG:
                        print('|'+cmd+'|')
                    str += cmd
        if DEBUG:
            print('------------------')
        lcd.home()
        lcd.message(str)

    def update(self, command):
        if DEBUG:
            print('do',command)
        if command == 'u':
            self.up()
        elif command == 'd':
            self.down()
        elif command == 'r':
            self.right()
        elif command == 'l':
            self.left()
        elif command == 's':
            self.select()
    def up(self):
        if self.curSelectedItem == 0:
            return
        elif self.curSelectedItem > self.curTopItem:
            self.curSelectedItem -= 1
        else:
            self.curTopItem -= 1
            self.curSelectedItem -= 1
    def down(self):
        if self.curSelectedItem+1 == len(self.curFolder.items):
            return
        elif self.curSelectedItem < self.curTopItem+DISPLAY_ROWS-1:
            self.curSelectedItem += 1
        else:
            self.curTopItem += 1
            self.curSelectedItem += 1
    def left(self):
        if isinstance(self.curFolder.parent, Folder):
            # find the current in the parent
            itemno = 0
            index = 0
            for item in self.curFolder.parent.items:
                if self.curFolder == item:
                    if DEBUG:
                        print('foundit')
                    index = itemno
                else:
                    itemno += 1
            if index < len(self.curFolder.parent.items):
                self.curFolder = self.curFolder.parent
                self.curTopItem = index
                self.curSelectedItem = index
            else:
                self.curFolder = self.curFolder.parent
                self.curTopItem = 0
                self.curSelectedItem = 0
    def right(self):
        if isinstance(self.curFolder.items[self.curSelectedItem], Folder):
            self.curFolder = self.curFolder.items[self.curSelectedItem]
            self.curTopItem = 0
            self.curSelectedItem = 0
        elif isinstance(self.curFolder.items[self.curSelectedItem], Widget):
            if DEBUG:
                print('eval', self.curFolder.items[self.curSelectedItem].function)
            eval(self.curFolder.items[self.curSelectedItem].function+'()')
        elif isinstance(self.curFolder.items[self.curSelectedItem], CommandToRun):
            self.curFolder.items[self.curSelectedItem].Run()

    def select(self):
        if DEBUG:
            print('check widget')
        if isinstance(self.curFolder.items[self.curSelectedItem], Widget):
            if DEBUG:
                print('eval', self.curFolder.items[self.curSelectedItem].function)
            eval(self.curFolder.items[self.curSelectedItem].function+'()')

# now start things up
wrapper = ClientWrapper()
client = wrapper.Client()
uiItems = Folder('root','')

dom = parse(configfile) # parse an XML file by name

top = dom.documentElement

ProcessNode(top, uiItems)

display = Display(uiItems)
display.display()

if DEBUG:
    print('start while')

while 1:
    if (lcd.buttonPressed(lcd.LEFT)):
        display.update('l')
        display.display()
        sleep(0.25)

    if (lcd.buttonPressed(lcd.UP)):
        display.update('u')
        display.display()
        sleep(0.25)

    if (lcd.buttonPressed(lcd.DOWN)):
        display.update('d')
        display.display()
        sleep(0.25)

    if (lcd.buttonPressed(lcd.RIGHT)):
        display.update('r')
        display.display()
        sleep(0.25)

    if (lcd.buttonPressed(lcd.SELECT)):
        display.update('s')
        display.display()
        sleep(0.25)