import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# me == my email address
# you == recipient's email address
me = "Build System ClearCase Report"
you = "mjlencze@ra.rockwell.com"
fp = open('scan_report.html', 'rb')
# Create a text/plain message
msg = MIMEText(fp.read(), 'html')
fp.close()

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = 'Scan Report'
msg['From'] = me
msg['To'] = you

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('ranasmtp01.ra.rockwell.com')
s.sendmail(me, [you], msg.as_string())
s.quit()
