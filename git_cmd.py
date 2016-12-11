import logging
import utility


log = logging.getLogger(__name__)
LOGLEVEL = log.getEffectiveLevel()

def add(gpath):
    gcmd = 'git add . --all'
    proc = utility.SubprocessTimeoutWrapper(gcmd, cwd = gpath)
    out, err = proc.communicate()
    if err is not None:
        for line in err.splitlines():
            log.warning(line)
    if out is not None and LOGLEVEL == logging.DEBUG:
       for line in out.splitlines():
           log.debug(line)

def commit(gpath, author, date, msg):
    gcmd = 'git commit --date {} --author="{} <{}@ra.rockwell.com>" -m "{}"'.format(date, author, author, msg)
    proc = utility.SubprocessTimeoutWrapper(gcmd, cwd = gpath)
    out, err = proc.communicate()
    if err is not None:
        for line in err.splitlines():
            log.warning(line)
    if out is not None: 
       for line in out.splitlines():
           log.debug(line)

def push(gpath, remote = 'origin'):
    gcmd = 'git push {}'.format(remote)
    proc = utility.SubprocessTimeoutWrapper(gcmd, cwd = gpath)
    out, err = proc.communicate()
    if err is not None:
        for line in err.splitlines():
            log.warning(line)
    if out is not None and LOGLEVEL == logging.DEBUG:
       for line in out.splitlines():
           log.debug(line)
