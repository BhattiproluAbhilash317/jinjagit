import datetime
import calendar
import logging
import time
import subprocess
import threading
import shlex


log = logging.getLogger(__name__)

class OmitFilter(logging.Filter):
    def __init__(self, name = None, function = None, level = None):
        self.name = name
	self.function = function
	self.level = level

    def filter(self, record):
        allow = True
	#print("name: {} func: {} level: {}".format(record.name, record.funcName, record.levelname))
        if self.name == record.name and self.function == record.funcName and self.level == record.levelname:
	    allow = False
        elif self.name == record.name and self.function == record.funcName and self.level is None:
	    allow = False
        elif self.name == record.name and self.function is None and self.level is None:
            allow = False
	return allow

class SubprocessTimeoutWrapperException(Exception):
    def __init__(self, timeout):
        self.timeout = timeout

    def __str__(self):
        return repr(self.timeout)

class SubprocessTimeoutWrapper(threading.Thread):
     """
     subprocess api has no timeout in python 2.  This is a quick workaround
     """
     def __init__(self, command, cwd = None, timeout = None):
         threading.Thread.__init__(self)
         self.daemon   = True
         self.process  = None
         self.command  = shlex.split(command)
         self.timeout  = timeout
         self.stdout   = None
         self.stderr   = None
         self.cwd      = cwd


     def run(self):
         self.process = subprocess.Popen(self.command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, cwd = self.cwd)
         #log.debug('started process name {} with pid {}'.format(self.command[0], self.process.pid))
         self.stdout, self.stderr = self.process.communicate()

         #    log.debug('waiting {} seconds for timeout'.format(self.timeout))
     def communicate(self):
         self.start() 
         if self.timeout is not None:
             self.join(self.timeout)
             if self.is_alive():
                 self.process.kill()
                 log.warn('process for command {} timed out'.format(self.command))
                 raise SubprocessTimeoutWrapperException(self.timeout)
             else: 
                 pass
                 #log.info('process exit ok')
         else:
            pass 
         
         self.join()
         #stderror is here
         return (self.stdout, self.stderr) 

def convert_str_to_datetime(timestamp):
    clk = timestamp[0:19]
    sgn = int(timestamp[-6] + '1')  # concatenate the + or - with a 1 and turn into int
    mns = int(timestamp[-2:]) * sgn
    hrs = int(timestamp[-5:-3]) * sgn
    dtime = datetime.datetime.strptime(clk, '%Y-%m-%dT%H:%M:%S')
    delta = datetime.timedelta(hours=hrs, minutes=mns)
    dtime = dtime - delta
    return dtime

def calc_diff_in_seconds(timestamp):
    current_time = convert_str_to_datetime(convert_epoch_iso8601(time.time(), tz='-05:00'))
    check_in_time = convert_str_to_datetime(timestamp)
    elapsedTime = current_time - check_in_time
    return elapsedTime.total_seconds()


def convert_iso8601_epoch(timestamp):
    """
    Takes ISO 8601 formatted string and converts into unix epoch time.
    parameters
    ---------------------------
    timestamp: string representation of an iso8601 timestamp: 2016-03-21T14:08:22-05:00
    return
    ---------------------------
    output integer representative of the number of seconds since 1970-01-01:00:00:00-00:00
    otherwise known as the unix epoch
    can only handle the exact format above of YYYY-MM-DDTHH:mm:ss!hh:zz
    """
    #log.debug("length: {}".format(len(timestamp)))
    #if len(timestamp) is not 25... value error?
    clk = timestamp[0:19]
    sgn = int(timestamp[-6]+'1') #concatenate the + or - with a 1 and turn into int
    mns = int(timestamp[-2:])*sgn
    hrs = int(timestamp[-5:-3])*sgn
    dtime = datetime.datetime.strptime(clk,'%Y-%m-%dT%H:%M:%S')
    delta = datetime.timedelta(hours=hrs, minutes=mns)
    dtime = dtime - delta
    sec = calendar.timegm(dtime.timetuple()) 
    return int(sec)

def convert_epoch_iso8601(epoch, tz = '+00:00'):
    """
    Takes a unix epoch and converts into iso8601 string
    input is a number of seconds since 1970-01-01:00:00:00
    tz is an iso8601 formated timezone, must be in format sHH:MM 
       where s is sign HH is hoursand MM is minutes. 
       for example central daylight time is -05:00
    output is an iso8601 formatted string.  
    """
    log.debug("convert: {} {}".format( epoch, tz ))
    sgn = int(tz[0] + '1')
    hrs = int(tz[1:3])*sgn
    mns = int(tz[4:])*sgn
    epoch_adjusted = epoch - ((hrs*3600) + (mns*60))*sgn
    tm = time.gmtime(epoch_adjusted)
    ts = time.strftime('%Y-%m-%dT%H:%M:%S', tm)
    ts = '{}{}'.format(ts,tz)
    return ts

def restructure_list_dict(ldict, key, dkey):
    """
    refactor a list of dictionaries by a particular key name
    parameter
    ldict is an input list of dictionaries
    key is a particular value that the list of dicts that represent  
    """
    #get set of unique key_values 
    key_values = set()
    rlist = list()
    for entry in ldict:
        if key in entry:
            key_values.add(entry[key])
    #parse array for key_values and reformat 
    out = []
    for val in key_values:
        matches = list()
        for element in ldict:
            if element[key] == val:
                cpy = dict(element)
                cpy.pop(key, None)
                matches.append(cpy)
        out.append({key: val, dkey: matches})
    return out
