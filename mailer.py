import logging 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import glob
import threading
import time
import json
import os
import re
import jinja2
from utility import calc_diff_in_seconds
from ldap_mail import ldap_get_mail, get_ldap_conn

log = logging.getLogger(__name__)

class SimpleBulkMailer(object):
    """SimpleBulkMailer is intended to provide a simple interface to automate
    sending several messages to an email server.
    messages are configured with the create_message function
    a send operation sends all 
    """

    def __init__(self, server, origin='SIMPLEMAILER', auth = None, timeout = 10):
        """ initialize this class with connection information to an email service
         
        """
        self.servername = server
        self.timeout = timeout
        self.auth = auth
        self.origin = origin
        self.messages = [] 
        log.debug('initialized {}'.format(self.servername))

    def create_message(self, subject, message, destination, origin = None, mime_type='html'):
        """ create a new message in the array of outgoing messages
        parameters:
        subject: string type to use for the subject of the email
        message: body part for the message
        destination: to email address
        origin: optionally can set messages with alternate From
        return:
        nothing, just sets up a new message in to be delivered in an internal array
        """
        msg = MIMEMultipart('alternative')
        if origin is not None:
            msg['From'] = origin
        else:
            msg['From'] = self.origin
        msg['Subject'] = subject
        msg['To'] = destination
        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred
        msg.attach(MIMEText(message, mime_type))
        self.messages.append(msg)

    def _connect_smtp(self):
        """ helper function to initiate connection to an SMTP server
            return
            smtplib.SMTP object
        """
        smtp = None
        try:
            smtp = smtplib.SMTP(self.servername, timeout = self.timeout)
        except smtplib.SMTPException as err:
            log.critical('smtp service at {} is not currently available'.format(self.servername))
            log.critical(err)
        except Exception as err:
            log.critical('smtp other error {} is not currently available'.format(self.servername))
            log.critical(err)
        
        if self.auth is not None:
            try:
                smtp.login(self.auth[0], self.auth[1])
            except smtplib.SMTPException as err:
                log.warn('smtp service login error for {}'.format(self.servername))
                log.warn(err)
        return smtp 

    def send(self):
        """
         perfoms a bulk send on all messages that have been set previously by
         create message. communication with email service is limited to this blocking
         function.
         parameters:
        """
        log.debug('send {} messages'.format(len(self.messages)))
        smtp = self._connect_smtp()
        if smtp is not None:
            for msg in self.messages:
                #log.debug('message: \n\r{}'.format(msg.as_string()))
                try:
                    smtp.sendmail(msg['From'], msg['To'], msg.as_string())
                except smtplib.SMTPRecipientsRefused as err:
                    log.warn('Recipient refused for following message: \n\r{}'.format(msg.as_string()))
                    log.warn(err)
		    continue
                except smtplib.SMTPException as err:
                    log.critical('something went wrong with sending message: \n\r{}'.format(msg.as_string()))
                    log.critical(err)
                except Exception as ex:
		    log.warn("unexpected Exception")
                    log.warn(ex)
                self.messages.remove(msg)
	    smtp.quit()
        else:
            log.warning('emails did not get sent because of exception in connection')

class MailManager(threading.Thread):

    def __init__(self, notifications_path, server, sender, subject, receiver, template_path, story_number_check, message_too_old=3600,
                 ldap_details=None):
        """
        dpath:  path to the dynamic view
        spath:  path to the snapshot view
        branch: branch associated with relevant views to look for history events
        """

        threading.Thread.__init__(self)
        self.daemon             = True
        self.bulk_mailer        = SimpleBulkMailer(server, sender)
        self.subject            = subject
        self.notifications_path = notifications_path
        self.template_path      = template_path
        self.receiver           = receiver
        self.story_number_check = story_number_check
        self.message_too_old    = message_too_old
        self.ldap_details = ldap_details

    @staticmethod
    def render(template_path, context):
        path, filename = os.path.split(template_path)
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(path or './')
        ).get_template(filename).render(context)

    def process_notifications(self):
        """
        glob module finds all the path names matching a specified pattern
        """
        json_patterns = os.path.join(self.notifications_path, '*.json')
        file_list = glob.glob(json_patterns)
        for fileName in file_list:
            #get the data from the file and then delete the file
            with open(fileName) as fp:
                data = json.loads(fp.read())
            os.remove(fileName)

            #make sure that the file 
            diff_seconds = calc_diff_in_seconds(data['time'])
            log.debug("message is {} seconds old".format(diff_seconds))
            if diff_seconds > self.message_too_old:
                log.warn('---------------------------------------------------------')
                log.warn('Timed out.... Ignoring the changes from sending mail.')
                log.warn('---------------------------------------------------------')
                continue


            # this the pilot rule to limit emails sent to individuals
	    if data['user'] in ['mjlencze', 'vbhatti', 'jcanderson', 'mttrader', 'prvadhavkar', 'wdstraw', 'jbvitran', 'mburedd', 'pbobba']:
	        log.info("user {} rule matches, sending email".format(data['user']))
	    else:
	        log.warn("user {} NOT matches rule.  not sending email")
	        continue

            email_addrs = ldap_get_mail(data['user'])
            log.debug("user {} email address {}".format(data['user'], email_addrs))
            no_story_number = False
            # check if story number is present in the comments
            if not re.search(self.story_number_check, data['comments']):
                no_story_number = True

            subject = self.subject.format(comments=data['comments'])

            context = dict(branch=data['branch'],
                           email_addrs='{},'.format(email_addrs),
                           epoch=data['time'],
                           names=data['names'],
                           comments=data['comments'],
                           no_story_number=no_story_number,
                           subject=subject)
            message = MailManager.render(self.template_path, context)
            # message = MIMEText(message, 'html')
            # message = self.template.format(branch=data['branch'], user=data['user'],
            #                                epoch=data['time'],
            #                                names=', '.join(names), comments=data['comments'])

            # uncomment the below line to send mail  to the committed user
            self.bulk_mailer.create_message(subject, message, email_addrs)
        self.bulk_mailer.send()

    def run(self):
        while True:
    	    log.debug("processing notifications!------------------------------------------------------------------------------")
            self.process_notifications()
            time.sleep(30)

