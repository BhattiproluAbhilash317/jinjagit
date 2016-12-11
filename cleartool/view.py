import os
import logging
import subprocess
import json 
import tempfile
import utility

log = logging.getLogger(__name__)

def start(vtag, timeout = None):
    """View registered with view_tag is started on local system
    """
    log.info('starting view: {}'.format(vtag))
    cleartool_cmd = 'cleartool startview {}'.format(vtag)
    proc = utility.SubprocessTimeoutWrapper(cleartool_cmd, cwd = view_path, timeout = timeout)
    output = proc.communicate()
    stdout = output[0]
    stderr = output[1]
    log.debug('stdout: {}'.format(stdout))
    log.error('stderr: {}'.format(stderr))

def end(vtag, timeout = None):
    """View that has been previously started with given view_tag is
    ended
    """
    log.info('ending view: {}'.format(vtag))
    cleartool_cmd = 'cleartool endview {}'.format(vtag)
    proc = utility.SubprocessTimeoutWrapper(cleartool_cmd, cwd = view_path, timeout = timeout)
    output = proc.communicate()
    stdout = output[0]
    stderr = output[1]
    log.debug('stdout: {}'.format(stdout))
    if stderr is not None:
        log.error('stderr: {}'.format(stderr))

def get_config_spec(view_path, timeout = None):
    """TODO: document me
    """
    cleartool_cmd = 'cleartool catcs'.format(view_path)
    log.info('Path for WD:' + view_path)
    proc = utility.SubprocessTimeoutWrapper(cleartool_cmd, cwd = view_path, timeout = timeout)
    output = proc.communicate()
    stdout = output[0]
    stderr = output[1]
    #TODO: errors if stderr contains information 
    #log.info('{}'.format(stdout))
    #log.error('{}'.format(stdout))
    return stdout 

def update_snapshot(view_path, timeout = None):
    """TODO: document me
    """
    cleartool_cmd = 'cleartool update .'.format(view_path)
    proc = utility.SubprocessTimeoutWrapper(cleartool_cmd, cwd = view_path, timeout = timeout)
    output = proc.communicate()
    stdout = output[0]
    stderr = output[1]
    #TODO: errors if stderr contains information 
    #log.info('{}'.format(stdout))
    #log.error('{}'.format(stdout))
    return stdout 

def set_config_spec(view_path, filename, timeout = None):
    """ this has different effects on different types of views
    """ 
    cleartool_cmd = 'cleartool setcs {}'.format(filename)
    proc = utility.SubprocessTimeoutWrapper(cleartool_cmd, cwd = view_path, timeout = timeout)
    output = proc.communicate()
    stdout = output[0]
    stderr = output[1]
    #TODO: errors if stderr contains information 
    #log.info('{}'.format(stdout))
    #log.error('{}'.format(stderr))


def get_cs_latest(view_path, timeout = None):
    """ 
    """
    current_config_spec = get_config_spec(view_path)
    ts = None
    for line in current_config_spec.split('\n'):
        if '-time ' in line:
            rep = line.split()
            index = rep.index('-time') + 1
            ts = rep[index]
            break
    res = 0
    if ts == None:
        res = time.time()
    else:
        res = utility.convert_iso8601_epoch(ts)+1
    return res

def set_cs_latest(view_path, latest, timeout = None):
    """
    the config spec time entry is updated
    """
    current_config_spec = get_config_spec(view_path)
    replacement = list()
    for line in current_config_spec.split('\n'):
        if '-time ' in line:
            rep = line.split()
            index = rep.index('-time') + 1
            rep[index] = latest
            result = ' '.join(rep) 
            replacement.append(result)
        else:
            replacement.append(line)
    #tmp = open('config_spec.txt', 'wb+')
    tmpfile = open(view_path+'\\cspec.txt', 'wb+')
    for line in replacement:
        tmpfile.write('{}\n'.format(line))
    tmpfile.close()
    #log.debug('temp file name: {}'.format(view_path+'\\cspec.txt'))
    set_config_spec(view_path, 'cspec.txt' )
    os.remove(view_path+'\\cspec.txt')

