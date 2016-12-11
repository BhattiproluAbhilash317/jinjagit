import os
import logging
import utility

log = logging.getLogger(__name__)

def copy(source, dest, view_path, timeout = None):
    log.debug('copy file {} to {}'.format(source,dest))
    if os.path.isfile(dest):
        try:
            os.remove(dest) 
        except WindowsError as snarflecookies:
            log.debug('fix permissions')
            os.chmod(dest, 0777)
            os.remove(dest) 

    cleartool_cmd = 'cleartool get -to {} {}'.format(dest, source)
    proc   = utility.SubprocessTimeoutWrapper(cleartool_cmd, cwd = view_path, timeout = timeout)
    output = proc.communicate()
    os.chmod(dest, 0777)
