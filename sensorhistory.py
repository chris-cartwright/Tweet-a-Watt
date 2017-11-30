import time, datetime
import sys
import traceback

class SensorHistories:
    # array of sensor data
    sensorhistories = []

    def __init__(self):
        self.sensorhistories = []
            
    def find(self, sensornum):
        for history in self.sensorhistories:
            if history.sensornum == sensornum:
                return history
        # none found, create it!
        history = SensorHistory(sensornum)
        self.sensorhistories.append(history)
        return history
                
    def __str__(self):
        s = ""
        for history in self.sensorhistories:
            s += history.__str__()
        return s
		
####### store sensor data and array of histories per sensor
class SensorHistory:
  sensornum = 0                # the ID for this set of data
  cumulative5mwatthr =  0      # data for power collected over last 5 minutes
  dayswatthr = 0               # power collected over last full day
  fiveminutetimer = 0
  lasttime = 0

  def __init__(self, sensornum):
      self.sensornum = sensornum
      self.fiveminutetimer = time.time()  # track data over 5 minutes
      self.lasttime = time.time()
      self.cumulative5mwatthr = 0
      self.dayswatthr = 0
      
  def addwatthr(self, deltawatthr):
      self.cumulative5mwatthr +=  float(deltawatthr)
      self.dayswatthr += float(deltawatthr)

  def reset5mintimer(self):
      self.cumulative5mwatthr = 0
      self.fiveminutetimer = time.time()
      
  def avgwattover5min(self):
      return self.cumulative5mwatthr * (60.0*60.0 / (time.time() - self.fiveminutetimer))
  
  def __str__(self):
      return "[ id#: %d, 5mintimer: %f, lasttime; %f, 5minwatthr: %f, daywatthr = %f]" % (self.sensornum, self.fiveminutetimer, self.lasttime, self.cumulative5mwatthr, self.dayswatthr)

