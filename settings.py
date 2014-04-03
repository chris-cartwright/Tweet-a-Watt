    
class Settings(object):
    def LOGFILENAME():
        return "powerdatalog.csv"   # where we will store our flatfile data

    def SERIALPORT():
        return "COM4"    # the com/serial port the XBee is connected to
    
    def BAUDRATE():
        return 9600      # the baud rate we talk to the xbee
    
    def CURRENTSENSE():
        return 4       # which XBee ADC has current draw data
    
    def VOLTSENSE():
        return 0          # which XBee ADC has mains voltage data
    
    def MAINSVPP():
        return 170 * 2     # +-170V is what 120Vrms ends up being (= 120*2sqrt(2))
    
    def VREFCALIBRATION():
        return [492,  # Calibration for sensor #0
                498,  # Calibration for sensor #1
                489,  # Calibration for sensor #2
                492,  # Calibration for sensor #3
                501,  # Calibration for sensor #4
                493]  # etc... approx ((2.4v * (10Ko/14.7Ko)) / 3
    
    def CURRENTNORM():
        return 15.5  # conversion to amperes from ADC
    
    def NUMWATTDATASAMPLES():
        return 1800 # how many samples to watch in the plot window, 1 hr @ 2s samples
    