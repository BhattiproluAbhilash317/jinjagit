"""    
basics to use this module:
   - clearcase view relating to only one VOB. multiple VOBS are not supported
   - the config spec of the view must contain a "LATEST" rule
   - set up two views 
      -snapshot: path to snapshot view is spath
      -dynamic:  path to dynamic view is dpath
   - in the snapshot view
       - configure the config spec LATEST rule with a time in the past and
         update the view
       - initialize a new git repository in the VOB subfolder
"""    
import cleartool.checkout
import cleartool.view
import cleartool.history
import Queue
import utility
import logging
import threading
import time
import git_cmd

log = logging.getLogger(__name__)

class CCGitInterpreter(threading.Thread):
    """
    this class interprets events from a clearcase dynamic view into logical
    change sets appropriate for a git revision control solution
    mostly this is done with several rules for analysis on the 'user' field
    and the reported time of each cleartool history entry
    """
     
    def __init__(self, dpath, spath, ccbranch):
        threading.Thread.__init__(self)
        self.daemon           = True
        self.spath            = spath
        self.dpath            = dpath
        self.MAX_TIME         = 45 
        self.PUSH_TIME        = 120 
        # this is a little cheap way of doing it, 
        # though logically some comments may get duplicated in interrupted
        # long term historical imports
        # a add one here so as not to pull time again
        scantime = cleartool.view.get_cs_latest(spath)+1 

        self.event_scanner    = cleartool.history.EventScanner(dpath, ccbranch, scantime)
        self.last_pull_time   = None 
        self.queue_empty_time = None 
        self.changes          = list()
        self.new_event        = None
        self.old_event        = None
        self.push_pending     = False

    def start(self):
        #get time of last successful update
        #begin_time = cleartool.utility.convert_iso8601_epoch("2016-08-12T18:00:00-05:00")
        #TODO: get this timestamp from the filesystem
        self.event_scanner.start()
        threading.Thread.start(self)

    def _change_user_check(self):
        """
        a difference in users indicates that the change set ended with previous user
        and a new change set begins with the current event.
        """
        if self.new_event is not None and self.old_event is not None:
            if self.new_event['user'] != self.old_event['user']:
                self.changes.append(dict(self.old_event))
                self.old_event = None
                return True
        return False
    
    def _change_time_check(self):
        """
        if a single user stays the same, but doesn't check in files for a while,
        the change set ended with previous event and  and a new change set begins 
        with the current event.
        """
        if self.new_event is not None and self.old_event is not None:
            tdelta = self.new_event['epoch'] - self.old_event['epoch']
            #log.debug('tdelta: {}'.format(tdelta))
            if tdelta > self.MAX_TIME: 
                self.changes.append(dict(self.old_event))
                self.old_event = None
                return True
        return False

    def _change_late_check(self):
        """
        if its been a really long time since the last change its time to
        flush both previous and current, then apply whatever is in the changes list
        returning true signalse it is time to apply the changes.  flush previous and current
        """
        tnow = time.time()
        if self.new_event is not None:
            age = tnow - self.last_pull_time
            if age > self.MAX_TIME:
                if self.old_event is not None:
                    self.changes.append(dict(self.old_event))
                    self.old_event = None
                self.changes.append(dict(self.new_event))
                self.new_event = None
                return True 
        return False
    
    def _change_push_check(self):
        # if the queue has been empty for a while and a push is needed
        if self.push_pending == True and self.queue_empty_time is not None:
            repo_sleep_time = time.time() - self.queue_empty_time
            #log.debug("sleep time: {}".format(repo_sleep_time))
            if repo_sleep_time > self.PUSH_TIME:
                log.debug("repo has been sleeping, push to central now")
                #TODO: PUSH TO CENTRAL REPO HERE
                git_cmd.push(self.spath)
                self.push_pending = False

    def _collect_comments(self):
        log.debug('changeset includes the comments')
        comments = ''
        new = '' 
        swp = '' 
        for change in self.changes:
	    if new != '':
                swp = new 
            new = change['comment'].decode('utf-8','ignore')
            if new != swp:
                comments = comments + new 
	comments = comments.replace('"','\\"')
	if comments == '':
	   comments = "empty comments disallowed in git"

        return comments 

    def _do_changes(self):
        log.debug('changeset includes the following events')
        for change in self.changes:
            log.debug('     {} {} {}'.format(change['date'], change['user'], change['name']))

        c_date = self.changes[-1]['date']
        c_user = self.changes[-1]['user']
        c_date = self.changes[-1]['date']

        cleartool.view.set_cs_latest(self.spath, c_date)
        
        c_comm = self._collect_comments()
        git_cmd.add(self.spath)
        git_cmd.commit(self.spath, c_user, c_date, c_comm)
        #TODO: only do the following if git command above are OK
	#FORNOW, is OK
        del self.changes[:]
        self.push_pending = True

    def _pull_event(self):
        """
        get an event
        """
        if self.event_scanner.queue.empty() == False:
            self.queue_empty_time = None
            if self.new_event is None and self.old_event is None:
                self.new_event = dict(self.event_scanner.queue.get())
                return True
            if self.new_event is not None and self.old_event is None:
                self.old_event = dict(self.new_event)
                self.new_event = dict(self.event_scanner.queue.get())
                return True
            if self.new_event is not None and self.old_event is not None:
                self.changes.append(dict(self.old_event))
                self.old_event = dict(self.new_event)
                self.new_event = dict(self.event_scanner.queue.get())
                return True
            if self.new_event is None and self.old_event is not None:
                log.debug('hmmm..... how did I get here? ')
        else:
            if self.queue_empty_time is None:
                self.queue_empty_time = time.time()
        return False

    def run(self):
        """
        there are a few possiblities with state changes here:
        one:   one lonely change is available for a really long time
        two:   the last group of changes were all made within the time threshold
               by the same user
        three: the previous change was performed by a different user than the 
               most recent change
        four:  the previous was performed by the same user, but happened quite 
               a while since the last change
        """
        while True:
            # try to get at least one event
	    # check for stuff in queue every 2 seconds
	    time.sleep(2)
            if self._pull_event():
                self.last_pull_time = time.time()
            
            if self._change_late_check():
                self._do_changes()
                continue

            if self._change_user_check():
                self._do_changes()
                continue

            if self._change_time_check():
                self._do_changes()
                continue

            if self._change_push_check():
                self._push_changes()

