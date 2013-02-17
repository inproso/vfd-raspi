#!/usr/bin/python

import RPi.GPIO as GPIO
import sched, time, datetime, signal
import spidev

# ===========================================================================
# SPI Clock Example using hardware SPI with SPIDEV
# 16 February 2013
# William B Phelps - wm@usa.net
# ===========================================================================

#CE0  = 8
#MISO = 9
#MOSI = 10
#SCLK = 11
S1 = 22
S2 = 27
S3 = 17  # alarm on/off

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(S1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(S2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(S3, GPIO.IN, pull_up_down=GPIO.PUD_UP)

spi = spidev.SpiDev()
spi.open(0,0)
spi.mode = 0
#spi.max_speed_hz = 250000
#spi.max_speed_hz = 10000

def SPI(b):
	b1 = [b]
	b2 = spi.xfer(b1)
	time.sleep(0.001)

def SPIwrite(str):
	for i in range(len(str)):
		SPI(ord(str[i]))

def setNum(n):
	SPI(0x88)
	SPI(n & 0xFF)
	SPI(n >> 8)

def setDots(d):
	SPI(0x85)  # dots
	SPI(d)

def setPos(n):
	SPI(0x89)  # position
	SPI(n)

def setBrt(b):
	SPI(0x80)  # brightness
	SPI(b)

def setDot(b):
	SPI(0x86)  # dot flag
	SPI(b)

def setDash(b):
	SPI(0x87)  # dash flag
	SPI(b)

print "Raspi VFD test1"

SPI(0x82)  # clear
SPIwrite("01234567")
#setDots(0b11111111)
time.sleep(1)
for b in range(0,10):
	setBrt(b)
	time.sleep(0.2)
#setDots(0b00110011)
#time.sleep(1)
#setDots(0b01010101)
SPI(0x82)  # reset

#timeString  = time.strftime("%I%M")
#print timeString

# Globals
S1status = False
S2status = False
S3status = False
saveTime = datetime.datetime.now()

def chkButtons():
	global S1push, S2push, menuState
	global S1status, S2status, S3status
	S1push = False
	S2push = False
	st1 = not GPIO.input(S1)
	st2 = not GPIO.input(S2)
	st3 = GPIO.input(S3)
	if (st1 != S1status):
		if (st1):
			S1push = True
#			print "S1 on"
			setDash(1)
		else:
#			print "S1 off"
			setDash(0)
		S1status = st1
	if (st2 != S2status):
		if (st2):
			S2push = True
#			print "S2 on"
			setDot(1)
		else:
#			print "S2 off"
			setDot(0)
		S2status = st2
	if (st3 != S3status):
		if (st3):
#			S3push = True
			print "S3 on"
			setDot(1)
		else:
			print "S3 off"
			setDot(0)
		S3status = st3

g_alarm = False
g_bright = 10

menuNames = ['', 'alarm   ', 'bright  ', 'end     ']
menuState = 0
menuTime = time.time

def menuAlarm():
	global menuState
def menuBright():
	global menuState
def menuEnd():
	global menuState
	time.sleep(0.5)
	menuState = 0
menu = { 1:menuAlarm, 2:menuBright, 3:menuEnd }

def doMenu():
	global menuState, menuTime
	menuState += 1
	menuTime = time.time()
	setDots(0)
	setPos(0)
	SPIwrite(menuNames[menuState])
	menu[menuState]()
	
def setAlarm():
	global g_alarm
	
def setBright():
	global g_bright
	g_bright = (g_bright+1) if (g_bright<10) else 0
	s = '{:>8}'.format(g_bright)
	setPos(0)
	SPIwrite(s)
	setBrt(g_bright)
	
def setEnd():
	s = 0
	
action = { 1:setAlarm, 2:setBright, 3:setEnd}

def doAction():
	global menuState, menuTime
	menuTime = time.time()  # reset menu timeout timer
	action[menuState]()

def showTime():
	global saveTime
	setPos(0)
	now = datetime.datetime.now()
	if (now.second != saveTime.second):  # run once a second
		saveTime = now
		if (now.second >= 57) and (now.second <= 59):  # show date
			timestr = '{:%y-%m-%d}'.format(now)
			SPIwrite(timestr)
			# Toggle dots during date display
			if (now.second % 2):
				setDots(0b00000001)
			else:
				setDots(0b00000000)
		else:
			timestr = '{:  %I%M%S}'.format(now)
			SPIwrite(timestr)
			# Toggle dots
			if (now.second % 2):
				setDots(0b00010101)
			else:
				setDots(0b00010100)
		# adjust brightness according to time
		if (now.second == 0):  # once a minute
			setBrt(2)  # dim briefly to show top of minute
			time.sleep(0.1)
			if (now.hour < 7) or (now.hour >= 22):
				setBrt(2)  # dim for night time
			elif (now.hour >= 18):
				setBrt(7)  # dim slightly
			else:
				setBrt(10)  # max bright

def sayBye():
	SPI(0x82)  # clear
	SPIwrite("  bye  ")
	time.sleep(2.0)
	SPI(0x82)  # clear
	exit(0)

def handleSigTERM(signum, frame):
	print "kill signal"
	sayBye()
def handleCtrlC(signum, frame):
	print "Ctrl-C"
	sayBye()

signal.signal(signal.SIGTERM, handleSigTERM)
signal.signal(signal.SIGINT, handleCtrlC)

# main loop - check buttons, do menu, display time
while(True):
	chkButtons()
	if (S1push):
		doMenu()
	elif (S2push):
		if (menuState > 0):
			doAction()
	if (menuState > 0):
		if (time.time() - menuTime > 3):
			menuEnd()
	else:
		showTime()
	# Wait 100 ms
	time.sleep(0.1)