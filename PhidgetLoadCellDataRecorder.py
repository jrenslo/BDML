#! /usr/bin/python

"""Copyright 2011 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__="Adam Stelmack"
__version__="2.1.8"
__date__ ="14-Jan-2011 2:29:14 PM"

"""
    edited by Jon Renslo for the BDML at Stanford
    August, 2013
"""

#Basic imports
import sys, os
from time import time as getCurrentTime
from time import sleep
from datetime import *
#Phidget specific imports
from Phidgets.PhidgetException import PhidgetException
from Phidgets.Devices.Bridge import Bridge, BridgeGain
from optparse import OptionParser


#Convenience functions

def displayDeviceInfo(bridge):
    print("|------------|----------------------------------|--------------|------------|")
    print("|- Attached -|-              Type              -|- Serial No. -|-  Version -|")
    print("|------------|----------------------------------|--------------|------------|")
    print("|- %8s -|- %30s -|- %10d -|- %8d -|" % (bridge.isAttached(), bridge.getDeviceName(), bridge.getSerialNum(), bridge.getDeviceVersion()))
    print("|------------|----------------------------------|--------------|------------|")
    print("Number of bridge inputs: %i" % (bridge.getInputCount()))
    print("Data Rate Max: %d" % (bridge.getDataRateMax()))
    print("Data Rate Min: %d" % (bridge.getDataRateMin()))
    print("Input Value Max: %d" % (bridge.getBridgeMax(0)))
    print("Input Value Min: %d" % (bridge.getBridgeMin(0)))

def setEnabledAllChannels(device, state):
    for i in range(0,device.getInputCount()):
        device.setEnabled(i, state)

def setGainAllChanels(device,gain):
    for i in range(0,device.getInputCount()):
        device.setGain(i,gain)


#Event Handler Callback Functions
def BridgeAttached(e):
    attached = e.device
    print("Bridge %i Attached!" % (attached.getSerialNum())) if options.verbose

def BridgeDetached(e):
    detached = e.device
    print("Bridge %i Detached!" % (detached.getSerialNum())) if options.verbose

def BridgeError(e):
    try:
        source = e.device
        print("Bridge %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))

def BridgeData(e):
    try:
        source = e.device
        savedData.append([e.index,float((getCurrentTime()-startTime)*1000), e.value,e.device.getSerialNum()])
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))

    #format: [index, timestamp, value, serial num]


#Main Program Code

#Set up command line flags

parser = OptionParser()
parser.add_option("-t", "--time", dest="time",
                  help="duration of test in s", default=10)
## note, datarate is slightly faster than specified. 
parser.add_option("-r", "--rate", dest="dataRate",
                  help="duration of test in s", default=100)
parser.add_option("-m", "--manualtime",dest="manuallength",
                  help="manually end the data collection", default=False, action="store_true")
parser.add_option("-q", "--quiet",dest="verbose",
                  help="hide console messages", default=True,
                  action="store_false")
(options, args) = parser.parse_args()
options.dataRate = int(options.dataRate)
options.time = int(options.time)

#Initialize data storage variables

startTime = getCurrentTime()
savedData = []

#each bridge is distinguished by a unique serial number
iBridgeSerials = [293183,293824,293749]

#list of bridge objects.  Access serial by lBridges[0].getSerialNum()
lBridges = []

#loop through bridges creating bridge objects
for serial in iBridgeSerials:
    print("---Opening %i...---"%serial) if options.verbose
    try:
        tempBridge = Bridge()
    except RuntimeError as e:
        print("Runtime Exception: %s" % e.details)
        print("Exiting....")
        exit(1)
    try:
        tempBridge.setOnAttachHandler(BridgeAttached)
        tempBridge.setOnDetachHandler(BridgeDetached)
        tempBridge.setOnErrorhandler(BridgeError)
        tempBridge.setOnBridgeDataHandler(BridgeData)
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Exiting....")
        exit(1)

    try:
        tempBridge.openPhidget(serial)
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Exiting....")
        exit(1)

    print("Waiting for attach....") if options.verbose

    try:
        tempBridge.waitForAttach(20000)
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        try:
            tempBridge.closePhidget()
        except PhidgetException as e:
            print("Phidget Exception %i: %s" % (e.code, e.details))
            print("Exiting....")
            exit(1)
        print("Exiting....")
        exit(1)
    else:
        lBridges.append(tempBridge)
        displayDeviceInfo(lBridges[len(lBridges-1)]) if options.verbose

#Configure settings on each bridge
for bridge in lBridges:
    print("---Configuring %i...---"%bridge.getSerialNum())
    try:
        print("Set data rate to %i ms ..." % (int(options.dataRate))) if options.verbose
        bridge.setDataRate(int(options.dataRate))
        sleep(2)

        gain = BridgeGain.PHIDGET_BRIDGE_GAIN_8
        gainTable = ['invalid',1,8,16,32,64,128,'unknown']
        
        print("Set Gain to %s..." % str(gainTable[gain])) if options.verbose
        ##  bridge.setGain(0, BridgeGain.PHIDGET_BRIDGE_GAIN_8)
        setGainAllChanels(bridge,gain)
        sleep(1)

        print("Enable the Bridge input for reading data...") if options.verbose
        setEnabledAllChannels(bridge,True)
    ##    bridge.setEnabled(0, True)
        ## sleeps briefly so the sensors can configure to take data correctly
        sleep(1)

    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        try:
            bridge.closePhidget()
        except PhidgetException as e:
            print("Phidget Exception %i: %s" % (e.code, e.details))
            print("Exiting....")
            exit(1)
        print("Exiting....")
        exit(1)

## reset data for the test
startTime = getCurrentTime()
savedData = []

#sleep while the callback function records data
if options.manuallength:
    print("Taking data... (enter to stop)")
    chr = sys.stdin.read(1)
else:
    print("Taking data for %i seconds...."% (options.time)) if options.verbose
    sleep(options.time)

#close all bridges
for bridge in lBridges:

    print("---Closing %i...---") if options.verbose

    try:
        print("Disable the Bridge input for reading data...") if options.verbose
        setEnabledAllChannels(bridge,False)
        sleep(1)
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        try:
            bridge.closePhidget()
        except PhidgetException as e:
            print("Phidget Exception %i: %s" % (e.code, e.details))
            print("Exiting....")
            exit(1)
        print("Exiting....")
        exit(1)

    try:
        bridge.closePhidget()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Exiting....")
        exit(1)

print("Done.") if options.verbose

#save data to file

now = datetime.today().__str__()[:-7]
lNow = now.split()
lNow[1:1] = "_"
filename = 'data/Phidget_test_'+''.join(lNow)+'.csv'

print("Outputting data to file: %s"%(filename)) if options.verbose
try:
    if 'data' not in os.listdir('.'):
        os.mkdir('data')
    f = open(filename,'w')

    #first line contains metadata: [rate, gain, length of dataset]
    #Matlab can only read csv files with numeric entries
    f.write(''+str(options.dataRate)+','+str(gainTable[gain]))
    f.write(',%i' % (len(savedData)))
    f.write('\n')
    for row in enumerate(savedData):
        for entry in row[1]:
            f.write(str(entry)+',')
        f.write('\n')
        if row[0]%1000==0:
            f.flush()
except IOError as e:
    print("File error %i %s" % (e.code, e.details))
    print("Exiting.....")
    exit(1)
except IndexError as e:
    print("Index error %s" % (e))
    print("data length: %i, %i" % (len(savedData)))
    print("row: %i col: %i" % (row, col))
    f.flush()
f.close()

##run the accompanying matlab script to plot the values
'''
sleep(2)
import os
command = "/Applications/MATLAB_R2012b.app/bin/matlab -nosplash -nodesktop -r \"filename=\'"+filename+"\';Phidget_data_reader\""
os.system(command)
sleep(1)        
'''
exit(0)
