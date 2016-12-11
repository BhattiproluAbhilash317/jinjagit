import os
import logging
import subprocess
import json 
import datetime
import time
import calendar

FILESCAN = 'hpcint.json'

def convert_iso8601_mepoch(timestamp):
    """Takes ISO 8601 format(string) and converts into epoch time.
    input string: 2016-03-21T14:08:22.147-05:00
    output integer: 1458551302147
    """
    #log.debug(timestamp)
    clk = timestamp[0:18]
    sgn = int(timestamp[-6]+'1') #concatenate the + or - with a 1 and turn into int
    hrs = int(timestamp[-2:-1])
    mns = int(timestamp[-5:-4])*sgn
    dtime = datetime.datetime.strptime(clk,'%Y-%m-%dT%H:%M:%S')
    delta = datetime.timedelta(hours=hrs, minutes=mns)
    dtime = dtime + delta
    sec = calendar.timegm(dtime.timetuple()) + dtime.microsecond/1000000.0
    return int(sec)



log = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s | %(levelname)-7s |  %(module)-15s | %(funcName)-20s | %(message)s' 

logging.basicConfig(format=LOG_FORMAT,level=logging.DEBUG)

log.debug('current time: {}'.format(time.time()))

all_checkouts = None
with open(FILESCAN) as scan_data:    
    all_checkouts = json.load(scan_data)


users = set()
for co in all_checkouts:
   users.add(co['user']) 

now = int(time.time())
TOO_OLD = 1209600

report_table = []
for user in users:
    log.info("user: {}".format(user))
    row = '<tr> <td class="user" colspan="4">{user}</td> </tr>'.format(user = user)
    report_table.append(row)
    for co in all_checkouts:
        if co['user'] == user:
            age = now - convert_iso8601_mepoch(co['date'])
            if age > TOO_OLD:
                row = """<tr class="violation"> 
                  <td class="date" width="150px">{date}</td> 
                  <td class="host" width="100px">{host}</td> 
                  <td class="view" width="200px">{view}</td> 
                  <td class="file" width="500px">{file}</td>
                </tr>""".format(date = co['date'], host = co['host'], view = co['view'], file=co['file'])
                report_table.append(row)
                log.info(row)
            else:
                row = """<tr> 
                  <td class="date" width="150px">{date}</td> 
                  <td class="host" width="100px">{host}</td> 
                  <td class="view" width="200px">{view}</td> 
                  <td class="file" width="500px">{file}</td>
                </tr>""".format(date = co['date'], host = co['host'], view = co['view'], file=co['file'])
                report_table.append(row)
                log.info(row)

report_string = '\n'.join(report_table)

html_doc = """<html>
    <head>
        <title>CHECKOUT SUMMARY REPORT</title>
        <style>
            table {{
                table-layout:fixed;
                width:1000;
                font-family:courier, monospace;
                font-size:10px;
                border:3px solid black;
            }}
            th, td {{
                padding: 3px;
                text-align: left;
                border: 1px solid black;
                color: black;
            }}
            .violation {{
                color: red;
                font-weight: bold;
            }}
            .date {{
                width: 150;
                white-space: nowrap;
                vertical-align: top;
             }}
            .host {{
                width: 100;
                white-space: nowrap;
                vertical-align: top;
            }}
            .view {{
                width: 200;
                white-space: nowrap;
                vertical-align: top;
            }}
            .file {{
                width: 500;
                word-wrap: break-word;
            }}
            .user {{
                font-family: courier, monospace;
                font-weight: bold;
                font-size: 200%;
            }}
        </style> 
    </head>
    <body>
        <table>
           <tr>
               <th class="date">date</th> 
               <th class="host">host</th> 
               <th class="view">view</th> 
               <th class="file">file</th>
          </tr>
        {report_string}
        </table>
    </body>
</html>
""".format(report_string = report_string) 


log.info(report_string)

with open("report.html", "w") as outfile:
    outfile.write(html_doc)





"""
            <tr> <td colspan="4">user</td> </tr>
            <tr> <th>host</th> <th>view</th> <th>file</th> <th>date</th> </tr>
            <tr> <td>USMKEAPPS913</td> <td>debrown1_hpc_view</td> <td>\PowerFlex_HPC\products\hpc_thermal\kernel\source\main.c</td> <td>2014-06-25T15:02:11-05:00</td> </tr>
"""
