import clearcase.checkout
import clearcase.view
import clearcase.changes
import clearcase.utility
import time
import logging


log = logging.getLogger(__name__)

def save_json(obj, fname):
    #TODO: utility function that could be expanded for file based persistence
    log.debug('saving object to json file {}'.format(fname))
    with open(fname, 'w+') as save_file:
        save_file.write(json.dumps(obj, indent=4))

def load_json(fname):
    res = None
    with open(fname) as savedfile:
        res = json.load(savedfile)
    return res

def iso8601_epoch():
    tst = clearcase.utility.convert_iso8601_epoch("2016-08-10T12:50:00-05:00")
    log.debug("given time: {}".format(tst))

    epoch = int(time.time()) 
    log.debug("time  now:  {}".format(epoch))

    sdiff = epoch - tst

    log.debug("in seconds: {}".format(sdiff))
    log.debug("in minutes: {}".format(sdiff/60))
    log.debug("in hours:   {}".format(sdiff/3600))


    log.debug("time  now:  {}".format(epoch))
    iso = clearcase.utility.convert_epoch_iso8601(epoch, tz = '-05:00')
    log.debug("iso 8601:   {}".format(iso))
    tst = clearcase.utility.convert_iso8601_epoch(iso)
    log.debug("given time: {}".format(tst))

def clearcase_checkouts(): 
    VIEW_PATHS = [
#        'M:\mjlencze_ModelBasedDesignR2015a\MEQ_MATLAB',
        'M:\mjlencze_powerflex_hpc_int_01\PowerFlex_HPC',
#        'M:\mjlencze_powerflex_libs_database_01\PowerFlex_Libs',
#        'M:\mjlencze_powerflex_libs_logic_parser\PowerFlex_Libs'
    ]

    checkouts = []
    for view_path in VIEW_PATHS: 
        checkouts = clearcase.checkout.get_checkouts(view_path, checkouts)

    log.debug("record count: {}".format(len(checkouts)))
 
    save_json(checkouts, 'checkouts.json')    

    res = clearcase.checkout.filter_by_age(checkouts, 1209600)

    save_json(res['old'], 'old.json')
    save_json(res['young'], 'young.json')
    
    log.debug("young: {}".format(len(res['young'])))
    log.debug("old:   {}".format(len(res['old'])))
    log.debug("total: {}".format(len(res['old'])+len(res['young'])))

    metrics = clearcase.checkout.metrics_by_user(res['old'])
    res = clearcase.checkout.restructure_checkout_data(checkouts)
    save_json(res, 'old_checkouts.json') 

def clearcase_view_startstop():
    ##bah
    clearcase.view.end('mjlencze_powerflex_hpc_int_01')
    clearcase.view.start('mjlencze_powerflex_hpc_int_01')

