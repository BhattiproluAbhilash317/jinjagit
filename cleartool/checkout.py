import os
import logging
import subprocess
import json 
import time
import utility

log = logging.getLogger(__name__)

def get_checkouts(view_path, checkouts):
    """
    cleartool is installed and can be called from the command line
    parameters
    view_path is a directory path on the local system managed by clearcase
    checkout_array 
    return all the checkouts associated with the provided view_path
    """
    log.debug("getting checkouts from {}".format(view_path))
    cleartool_cmd = 'cleartool lsco -all -fmt %u-|-%d-|-%Tf-|-%n-|-%hEOR-|-'
    proc = utility.SubprocessTimeoutWrapper(cleartool_cmd, cwd = view_path, timeout = timeout)
    output = proc.communicate()
    stdout = output[0]
    stderr = output[1]
    log.debug('stdout: {}'.format(stdout))
    log.error('stderr: {}'.format(stderr)) 
    
    records = list()
    sane = stdout.decode('utf8', 'ignore')
    for line in sane.split('EOR-|-'):
        if line == '':
           continue
        rec = dict() 
        try: 
            parse = line.split('-|-')
            rec['user']=parse[0].lower()
            rec['date']=parse[1]
            rec['view']=parse[2]
            rec['file']=parse[3]
            rec['host']=parse[4]
        except Exception as ex:
            log.warning('checkout history entry output resulted in an unexpected exception')
            log.warning('exception {}'.format(ex))
            continue
        records.append(rec)
    log.info('total records: {}'.format(len(checkouts)))
    return records 

def filter_by_age(checkouts, age):
    """
    checkouts is an unprocessed clearcase checkout dump from get checkouts
    returns a dictionary with three entries for logical filter results
    """
    time_now = int(time.time())
    greater = list()
    lesser = list()
    equal = list()
    for checkout in checkouts:
        co = dict(checkout)
        file_epoch = utility.convert_iso8601_epoch(co['date'])
        co_age = time_now - file_epoch
        if co_age < age: 
            greater.append(co)
        elif co_age > age: 
            lesser.append(co)
        else:
            equal.append(co)
    res = {'greater':greater, 'lesser':lesser, 'equal':equal } 
    return res 

def restructure_checkout_data(checkouts):
    """
    reorganize the data so its more amenable to generate email reports:
    user - host - view - (file-date) hierarchial view
    user can have one or more hosts
    a host can have one or more views
    each view contains actual file - date pairs
    returns a list - dict hierarchy like so:
    [{ 'user':'username', 'checkouts': ['host': 'hostname1', 'views': [ 'veiw':'viewname1', 'files': [ 'file': 'filenameone', 'date':'codate' ] ] ] } ]
    """
    res = utility.restructure_list_dict(checkouts, 'user', 'checkouts')
    i = 0
    while i < len(res):
        cos = res[i]['checkouts']
        vws = utility.restructure_list_dict(cos, 'host', 'views')
        j = 0
        while j < len(vws):
            fco = vws[j]['views']
            fls = utility.restructure_list_dict(fco, 'view', 'files')
            vws[j]['views'] = fls
            j = j+1
        res[i]['checkouts'] = vws
        i = i+1
    return res 

def test_restructure(checkouts):
    """ just make sure that the checkout data is consitent
    """
    res = restructure_checkout_data(checkouts)
    foo = list()
    for users in res:
        user = users['user']
        for hosts in users['checkouts']:
            host = hosts['host']
            for views in hosts['views']:
                view = views['view']
                for fentry in views['files']:
                    fname = fentry['file']
                    date = fentry['date']
                    foo.append([date, host, user, fname, view])
    foo.sort()                        
    with open('res.txt', 'w+') as testfile:
        for ent in foo:
            testfile.write('{}\n'.format(str(ent)))

    bar = list()
    for co in checkouts:
        bar.append([co['date'], co['host'], co['user'], co['file'], co['view']])
    
    bar.sort()                        
    with open('tst.txt', 'w+') as testfile:
        for ent in bar:
            testfile.write('{}\n'.format(str(ent)))

def metrics_by_user(checkouts):
    """ overall reporting backend
        counts up the checkout data to find which user has 
        files checked out.
    """
    res = restructure_checkout_data(checkouts)
    metrics = list()
    total = 0
    for element in res:
        i = 0
        j = 0
        k = 0
        user = element['user']
        for host in element['checkouts']:
            i = i+1
            for view in host['views']:
                j = j+1
                for fila in view['files']:
                    k = k+1
        log.debug('user: {:8} host: {:2} view: {:2} files: {:3}'.format(user, i, j, k))
        record = {'user':user, 'host':i, 'view':j, 'files':k}
        metrics.append(record)
        total = total + k 
    log.debug('total files in checkouts: {}'.format(total))
    return metrics
