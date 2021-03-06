#!/usr/bin/env python
import serial, time, datetime, sys, binascii
from xbee import xbee
from influxdb import InfluxDBClient
import sensorhistory
from settings import Settings

DEBUG = False
if (sys.argv and len(sys.argv) > 1):
    if sys.argv[1] == "-d":
        DEBUG = True
#print(DEBUG)

# open up the FTDI serial port to get data transmitted to xbee
ser = serial.Serial(Settings.SERIALPORT(), Settings.BAUDRATE())

sensorhistories = sensorhistory.SensorHistories()

# the 'main loop' runs once a second or so
def update_graph(idleevent):
    global avgwattdataidx, sensorhistories, DEBUG
     
    # grab one packet from the xbee, or timeout
    packet = xbee.find_packet(ser)
    if not packet:
        return        # we timedout
		
    if DEBUG:
        print(packet)
    
    xb = xbee(packet)             # parse the packet
    #print(xb.address_16)
    if DEBUG:       # for debugging sometimes we only want one
        print(xb)
        
    # we'll only store n-1 samples since the first one is usually messed up
    voltagedata = [-1] * (len(xb.analog_samples) - 1)
    ampdata = [-1] * (len(xb.analog_samples ) -1)
    # grab 1 thru n of the ADC readings, referencing the ADC constants
    # and store them in nice little arrays
    for i in range(len(voltagedata)):
        voltagedata[i] = xb.analog_samples[i+1][Settings.VOLTSENSE()]
        ampdata[i] = xb.analog_samples[i+1][Settings.CURRENTSENSE()]

    if DEBUG:
        print("ampdata: "+str(ampdata))
        print("voltdata: "+str(voltagedata))
		
    # get max and min voltage and normalize the curve to '0'
    # to make the graph 'AC coupled' / signed
    min_v = 1024     # XBee ADC is 10 bits, so max value is 1023
    max_v = 0
    for i in range(len(voltagedata)):
        if (min_v > voltagedata[i]):
            min_v = voltagedata[i]
        if (max_v < voltagedata[i]):
            max_v = voltagedata[i]

    # figure out the 'average' of the max and min readings
    avgv = (max_v + min_v) / 2
    # also calculate the peak to peak measurements
    vpp =  max_v-min_v

    for i in range(len(voltagedata)):
        #remove 'dc bias', which we call the average read
        voltagedata[i] -= avgv
        # We know that the mains voltage is 120Vrms = +-170Vpp
        voltagedata[i] = (voltagedata[i] * Settings.MAINSVPP()) / vpp

    # normalize current readings to amperes
    for i in range(len(ampdata)):
        # VREF is the hardcoded 'DC bias' value, its
        # about 492 but would be nice if we could somehow
        # get this data once in a while maybe using xbeeAPI
        if Settings.VREFCALIBRATION()[xb.address_16]:
            ampdata[i] -= Settings.VREFCALIBRATION()[xb.address_16]
        else:
            ampdata[i] -= Settings.VREFCALIBRATION()[0]
        # the CURRENTNORM is our normalizing constant
        # that converts the ADC reading to Amperes
        ampdata[i] /= Settings.CURRENTNORM()

    #print("Voltage, in volts: ", voltagedata)
    #print("Current, in amps:  ", ampdata)

    # calculate instant. watts, by multiplying V*I for each sample point
    wattdata = [0] * len(voltagedata)
    for i in range(len(wattdata)):
        wattdata[i] = voltagedata[i] * ampdata[i]

    # sum up the current drawn over one 1/60hz cycle
    avgamp = 0
    # 16.6 samples per second, one cycle = ~17 samples
    # close enough for govt work :(
    for i in range(17):
        avgamp += abs(ampdata[i])
		
    avgamp /= 17.0
	
    # sum up the current drawn over one 1/60hz cycle
    avgvolt = 0
    # 16.6 samples per second, one cycle = ~17 samples
    # close enough for govt work :(
    for i in range(17):
        avgvolt += abs(voltagedata[i])
		
    avgvolt /= 17.0

    # sum up power drawn over one 1/60hz cycle
    avgwatt = 0
    # 16.6 samples per second, one cycle = ~17 samples
    for i in range(17):         
        avgwatt += abs(wattdata[i])
		
    avgwatt /= 17.0

    if DEBUG:
        # Print out our most recent measurements
        print(str(xb.address_16)+"\tCurrent draw, in amperes: "+str(avgamp))
        print("\tWatt draw, in VA: "+str(avgwatt))

    if (avgamp > 13):
        return            # hmm, bad data

	# retreive the history for this sensor
    sensorhistory = sensorhistories.find(xb.address_16)
    #print(sensorhistory)
    
    # add up the delta-watthr used since last reading
    # Figure out how many watt hours were used since last reading
    elapsedseconds = time.time() - sensorhistory.lasttime
    dwatthr = (avgwatt * elapsedseconds) / (60.0 * 60.0)  # 60 seconds in 60 minutes = 1 hr
    sensorhistory.lasttime = time.time()
    if DEBUG:
        print("\t\tWh used in last ",elapsedseconds," seconds: ",dwatthr)

    sensorhistory.addwatthr(dwatthr)
    
    influx = InfluxDBClient(Settings.INFLUX_HOST(), 8086, database='Tweet-a-Watt')
    influx.write_points([{
        'measurement': 'usage',
        'tags': {
            'sensor': xb.address_16
        },
        'fields': {
            'Amps': avgamp,
            'Volts': avgvolt,
            'WattHours': dwatthr
        }
    }])
    
    # Determine the minute of the hour (ie 6:42 -> '42')
    currminute = (int(time.time())/60) % 10
    # Figure out if its been five minutes since our last save
    if (((time.time() - sensorhistory.fiveminutetimer) >= 60.0)
        and (currminute % 5 == 0)
        ):
        # Print out debug data, Wh used in last 5 minutes
        avgwattsused = sensorhistory.avgwattover5min()

        if DEBUG:
            print(time.strftime("%Y %m %d, %H:%M")+", "+str(sensorhistory.sensornum)+", "+str(sensorhistory.avgwattover5min())+"\n")
        
        # Reset our 5 minute timer
        sensorhistory.reset5mintimer()
        
if __name__ == "__main__":
    while True:
        update_graph(None)
