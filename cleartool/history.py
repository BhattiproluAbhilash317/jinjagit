import os
import logging
import json 
import time
import utility

log = logging.getLogger(__name__)


def _parse_output(data, vpath):
    """
    helper function that parses history from clearcase history opertations
    data is an object that contains output from clearcase lshistory command with format string
        %d-|-%u-|-%o-|-%n-|-%m-|-%cEOR-|-
        %d-|-%u-|-%o-|-%m-|-%n-|-%En-|-%cEOR-|-
    """
    vob_name = os.path.basename(vpath)
    records = list()
    if data is None:
        return records 
    # sanitize the data so the whole data chunk is now UTF8
    sane = data.decode('utf8', 'ignore')
    for line in sane.split('EOR-|-'):
        if line == '':
            continue
        rec = dict() 
        try:
            parse = line.split('-|-')          #TODO: if parse is NOT length 6, there is likely an error in the data.
            rec['date']      =parse[0]         #TODO: validate: is an iso8601 datestamp
            rec['epoch']     =utility.convert_iso8601_epoch(parse[0]) #this will cause value error exception if not iso8601
            rec['user']      =parse[1].lower() #TODO: validate: matches username format
            rec['operation'] =parse[2]         #TODO: validate: matches operation values
            rec['kind']      =parse[3]
            rec['name']      =parse[4].replace(vpath, '')
            rec['comment']   =parse[5]         #TODO: this is free text comment for history events 
        except Exception as ex:
            log.warning('attempt at parsing event history output resulted in an unexpected exception')
            log.warning('exception {}'.format(ex))
            continue
        records.append(rec)
    return records 

def request_events(view_path, since_time, branch, timeout = None,  filename = None):
    """
    view_path is the path to a mounted view
    since_time is date time argument for clearcase since
       Examples included here:
       https://www.ibm.com/support/knowledgecenter/SSSH27_8.0.1/com.ibm.rational.clearcase.cc_ref.doc/topics/ct_lshistory.htm
       iso8061 formated timestamps work just fine
    branch is a specific branch in the view
    if filename is provided, the output data is saved to give filename
    """
    log.debug("view {} since {} branch {} timeout: {}".format(view_path, since_time, branch, timeout))
    cleartool_cmd = 'cleartool lsh -since {} -all -nco -fmt %d-|-%u-|-%o-|-%m-|-%n-|-%cEOR-|- -bra {}'.format(since_time, branch)
    proc = utility.SubprocessTimeoutWrapper(cleartool_cmd, cwd = view_path, timeout = timeout)
    output = proc.communicate()
    stdout = output[0]
    stderr = output[1]
    #TODO: warn on error

    if stdout is not None and filename is not None:
        log.debug('saving to {}'.format(filename))
        with open(filename, 'wb+') as savefile:
            savefile.write(view_path+'\n')
            savefile.write(stdout)
    return _parse_output(stdout, view_path)

def load_events(filename):
    """
    parse a file with a set of changes from a clearcase VOB
    the file was created from the output of list_history_events 
    convienence function for analysis
    """
    changes = list()
    file_data = None
    with open(filename, 'rb+') as savefile:
        view_path = savefile.readline().strip()
        log.debug("view_path: {}".format(view_path))
        file_data = savefile.read() 
    return _parse_output(file_data, view_path)

def dump_to_file(view_path, time_since, file_root, branch = None):
    """
    little bit redundant function, but useful to simplify an export of the
    event history since a particular date
    """
    bin_file = '{}.bin'.format(file_root)
    json_file = '{}.json'. format(file_root)
    log.debug('dumping history to bin {} bin_file and attempting json conversion in {}'.format(bin_file, json_file))
    events = request_events(view_path, time_since, filename = bin_file, branch = branch) 
    with open(json_file, 'w+') as save_file:
        save_file.write(json.dumps(events, indent=4))

    #stderr = output[1]
    #log.debug('stdout: {}'.format(stdout))
    #if len(stderr.split()) > 0:
    #    log.warning('{} executed with output in stderr'.format(cleartool_cmd))
#	 log.warning('    {}'.format(stderr))
#	for line in stderr.splitlines():
#            log.warning('     {}'.format(line))

