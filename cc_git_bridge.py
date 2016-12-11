"""

   Need to divorce this from the local system time entirely
   Cannot assume that the local system time and the server time are in synch

   Can assume that both systems measure time the same way

   Startup:  get local base time (to compute local time differences)
             get historical time 

   start scanning
   request_events:  
   if successful: 
       record time elapsed since last event_request
   if unsucessful:

"""
import threading
import time
import Queue
import cleartool.history
import cleartool.view
import logging
import git_cmd
import re
import utility
import json
import uuid

THREAD_NAME = threading.currentThread().getName()

log = logging.getLogger(THREAD_NAME)


class ChangeSet(object):
     """
         one change contains a user, epoch, names of changes, and comments
     """
     def __init__(self, age = 30): 
        self.age   = age 
        self.user  = None 
        self.epoch = None
	self.names = list()
        self.comm  = '' 

     def contains(self, name):
         """if the current change set contains the change described by event
	 return True
	 """
	 if name in self.names:
	     return True
	 return False
     
     def _user_rule(self, user):
	 if self.user is None:
	     self.user = user 
         elif self.user != user:
             #log.debug("epoch Rule: {} {}".format(user, self.user))
             return False
	 return True

     def _epoch_rule(self, epoch):
	 if self.epoch is None:
	     self.epoch = epoch
         else:
             age = epoch - self.epoch
             #log.debug("epoch Rule: {}".format(age))
             if age > self.age:
                 return False
             else:
                 self.epoch = epoch
         return True

     def _collect_comment(self, comment):
         comm = comment.decode('utf-8', 'ignore')
         if comm == '':
             pass
         elif self.comm.endswith(comm) == False:
             self.comm = self.comm + comm

     def append_event(self, event):
         """ if the event user matches and the epoch is in the age range of the
         latest event appended to this change set return True.  otherwise, the
         change set is complete and the event was not appended
         """
         log.debug('LOGGING EVENT: {} {} {}'.format(event['user'], event['epoch'], event['name']))

	 if self._user_rule(event['user']) == False:
	     return False
       
         if self._epoch_rule(event['epoch']) == False:
	     return False
	
	 if self.contains(event['name']) == False:
	     self.names.append(event['name'])
             self._collect_comment(event['comment'])

         return True

     def is_empty(self):
         if self.user is None:
             return True
         return False 



class ChangeSetManager(object):
    """ This class manages a Queue object full of ChangeSets
    """
    def __init__(self):
        self.present     = ChangeSet()       # present ChangeSet 
        self.changes     = list()     # a queue of all change sets
	self.latest      = 0
        self.SLEEP_LONG  = 30                #
        self.SLEEP_SHORT = 30                #
        self.sleep_time  = 0

    def _process_event(self, event):
        """ append event to changeset
	if this is not successful put the change set in pending changes
	and start a new changeset with the current event
	"""
        self.latest = event['epoch']  
        if self.present.append_event(event) == True:
            pass 
        else:
            self.changes.append(self.present)
            self.present = ChangeSet()
	    self.present.append_event(event)

    def parse(self, events):
        """ a list of events is parsed into a list of changesets
	"""
        if len(events) == 0:
	    self.latest = self.latest + self.sleep_time - 1
            log.debug("No New Changes!")
        else:
	    log.info("one or more new events found")
            if self.present.is_empty() == True: 
                for event in reversed(events):
                    self._process_event(event)
            else:
                log.debug("NOT EMPTY user: {}".format(self.present.user))
                #if first event name in the incomming block is identical to last 
                #event name in the present changeset, then this is the SECOND time 
                #that this event has been observed and the events can be submitted
                if events[0]['name'] == self.present.names[-1]:
                    self.changes.append(self.present)
                    self.present = ChangeSet()
                    self.latest = self.latest + self.sleep_time - 1
                else:
                    for event in reversed(events):
                        self._process_event(event)
	    self.sleep_time = self.SLEEP_SHORT

    def __iter__(self):
        return iter(self.changes)

class ClearCaseGitBridge(threading.Thread):
    """ a snapshot view is configured with a the following requirements
            -the spath references the snapshot view vob root 
            -one and only one VOB 
	    -one and only one clearcase branch
            -the config_spec is configured with a time rule on the LATEST that
	      specifies a specific date in the branch history

        a git repository is initialized within the snapshot view
	        -git related files and folders must stay VIEW PRIVATE
	        -checked out named branch
		-the git remote origin is configured that tracks the named branch 
	        
        a dynamic view is configured with the following requriments
	    -the dpath reverences the dynamic view vob root
	    -the view configuration mirrors the snapshot view
	        -the time rule on the view configuration is NOT included
	    -the vob associated with the dynamic view is mounted
    """
    def __init__(self, dpath, spath, branch):
        """
        dpath:  path to the dynamic view
        spath:  path to the snapshot view
        branch: branch associated with relevant views to look for history events 
        """
        threading.Thread.__init__(self)
        self.name              = branch
        self.daemon            = True
        self.dpath             = dpath
	self.spath             = spath
        self.branch            = branch
        self.changes           = ChangeSetManager()
	self.changes.latest    = cleartool.view.get_cs_latest(spath) - 1
	self.push_pending      = False
	self.PUSH_TIME         = 180
	self.latest_change_age = 0
	self.log               = logging.getLogger(branch)
	formatter              = logging.Formatter("%(asctime)s | %(name)-10s | %(levelname)-8s |  %(module)-16s | %(funcName)-21s | %(message)s")
        handler                = logging.handlers.RotatingFileHandler(filename = 'log/{}.log'.format(branch))
        handler.setFormatter(formatter)
	self.log.addHandler(handler)

    def _log_change(self, changeset):
	self.log.info('-BEGIN-CHANGE-------------------------------------------------------------------')
        self.log.info('user:   {:10} '.format(changeset.user))
        self.log.info('time:   {:10} '.format(utility.convert_epoch_iso8601(changeset.epoch, tz='-05:00')))
        self.log.info('branch: {}    '.format(self.branch))
        for line in changeset.comm.splitlines():
            self.log.info('    {}'.format(line)) 
	self.log.info('     change includes following file versions')
        names = []
        res = ''
	for name in changeset.names:
	    name_version = name.split('@@')
	    if len(name_version) == 2:
	        file_name = name_version[0]
	        ver_name = name_version[1].split('\\')[-1]
		try:
		    int(ver_name)
	            res = '    {:4} {}'.format(ver_name, file_name)
	            self.log.info(res)
                except ValueError:
                    res = '    new  {}'.format(file_name)
	            self.log.info(res)
            else:
                res = '    {}'.format(name)
	        self.log.info(res)
            names.append(res)
        changeset_log = {
           'user'     : changeset.user,
           'time'     : utility.convert_epoch_iso8601(changeset.epoch, tz='-05:00'),
           'branch'   : self.branch,
           'names'    : names,
           'comments' : changeset.comm
        }
        notification_file = 'notifications/{}.json'.format(str(uuid.uuid4()))
        #SAVE the data for notification sending later on
        with open(notification_file, 'w+') as save_file:
            save_file.write(json.dumps(changeset_log))

        self.log.info(json.dumps(changeset_log, indent = 2))
	self.log.info('-END---CHANGE-------------------------------------------------------------------')

    def _update_snapshot(self, changeset):
        """the changeset.epoch is increased by one to ensure the last element 
	change is represented in the updated snapshot view.  otherwise, its
	missing until the next update and conversly commit.  The original 
	timestamp text representation is returned so its right in the git log
	TODO: THIS is where we could get stuck indefinitely
	"""
	ts = time.time()
        commit_time = utility.convert_epoch_iso8601(changeset.epoch, tz='-05:00')
        snapshot_time = utility.convert_epoch_iso8601(changeset.epoch+1, tz='-05:00')
        cleartool.view.set_cs_latest(self.spath, snapshot_time)
	te = time.time()
	self.log.debug('time to update: {}'.format(te - ts))
	return commit_time 

    def _process_comments(self, changeset):
        """ helper function to modify the changeset comments before making the
	a commit
	"""
	comment = changeset.comm 
        if comment == '':
	    comment = 'empty comment\n'
        comment = comment + '\n' + 'changeset includes clearcase element revisions\n'
	for name in changeset.names:
	    name_version = name.split('@@')
	    nv = ''
	    if len(name_version) == 2:
	        file_name = name_version[0]
	        ver_name = name_version[1].split('\\')[-1]
		try:
		    i = int(ver_name)
		    if i > 0:
		        fn = file_name.replace('\\','/')
			if fn[0] == '/':
			    fn = fn[1:]
	                nv = '    {:5} {}'.format(i, fn)
                except ValueError:
		    pass
            if nv != '':
	        comment = comment + nv + '\n'
        comment = comment.replace('"','\\"')
	return comment

    def _apply_change(self, changeset):
        """ performs the git commit
	"""
        timestamp = self._update_snapshot(changeset) 
        comment = self._process_comments(changeset)
        git_cmd.add(self.spath)
        git_cmd.commit(self.spath, changeset.user, timestamp, comment)
	self.push_pending = True

    def _push_repository(self, latest_change_age):
	self.log.debug("last change occured {} seconds ago".format(latest_change_age))
	if self.push_pending == True:
	    if latest_change_age >= self.PUSH_TIME:
	        self.log.info("pushing all changesets to remote")
	        git_cmd.push(self.spath)
		self.push_pending = False

    def _get_events(self):
        """
        """
        timeout = 20
        events = None
        while events is None:
            time_since = utility.convert_epoch_iso8601(self.changes.latest, tz ='-05:00')
            try:
                events = cleartool.history.request_events(self.dpath, time_since, self.branch, timeout = timeout)
                break
            except utility.SubprocessTimeoutWrapperException as ex:
                self.log.error('event request exception: {}'.format(ex.message))
                timeout = timeout + timeout
                self.log.error('timeout increased to {}'.format(timeout))
                continue
        self.changes.parse(events)

    def run(self):
        self.log.debug("START LOG------------------------------------------------------------------------------------------------------------------------------")
        latest_change_age = 0
        while True:
            self._get_events()
            for changeset in self.changes:
                if changeset.is_empty() == True:
                    log.warn("Empty Changeset found....")
                    continue
                latest_change_age = 0
                self._log_change(changeset)
                self._apply_change(changeset)
                self.changes.changes = list()
            #check for push changes
            #self._push_repository(latest_change_age)
            time.sleep(self.changes.sleep_time)
            latest_change_age = latest_change_age + self.changes.sleep_time
