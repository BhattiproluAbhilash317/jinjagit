import logging.config
import json
import time
from cc_git_bridge import ClearCaseGitBridge
from mailer import MailManager

if __name__ == "__main__":
    log = logging.getLogger(__name__)
    LOG_FORMAT = '%(asctime)s | %(levelname)-6s |  %(module)-10s | %(funcName)-30s | %(message)s' 
    logging.basicConfig(format=LOG_FORMAT,level=logging.DEBUG)
    cfg = None
    with open('config.json') as cfg_file:
        cfg = json.load(cfg_file)
    logging.config.dictConfig(cfg['logging'])

    log.info('------------------------------------------------------------------------------------------------------------------------------------')
    log.info('  ______     ______   ______     ______     ______      ______   ______     ______     ______     ______     ______     __    __    ')
    log.info(' /\  ___\   /\__  _\ /\  __ \   /\  == \   /\__  _\    /\  == \ /\  == \   /\  __ \   /\  ___\   /\  == \   /\  __ \   /\ "-./  \   ') 
    log.info(' \ \___  \  \/_/\ \/ \ \  __ \  \ \  __<   \/_/\ \/    \ \  _-/ \ \  __<   \ \ \/\ \  \ \ \__ \  \ \  __<   \ \  __ \  \ \ \-./\ \  ') 
    log.info('  \/\_____\    \ \_\  \ \_\ \_\  \ \_\ \_\    \ \_\     \ \_\    \ \_\ \_\  \ \_____\  \ \_____\  \ \_\ \_\  \ \_\ \_\  \ \_\ \ \_\ ')
    log.info('   \/_____/     \/_/   \/_/\/_/   \/_/ /_/     \/_/      \/_/     \/_/ /_/   \/_____/   \/_____/   \/_/ /_/   \/_/\/_/   \/_/  \/_/ ')
    log.info('------------------------------------------------------------------------------------------------------------------------------------')
	                                                                                                                                   

    log.info('current version!!!!')

    #for brg in cfg['ccgit']:
    #    log.debug('setting up bridge for {}'.format(brg['branch']))
    #    brg['instance'] = ClearCaseGitBridge(brg['dpath'], brg['spath'], brg['branch'])
    #    brg['instance'].start()

    mail_config = cfg['mail']
    ldap_config = cfg.get('ldap')
    mail_manager = MailManager(mail_config['notifications_path'], mail_config['server'], mail_config['sender'],
                               mail_config['subject'], mail_config['receiver'], mail_config['template_path'],
                               mail_config['story_number_check'],  ldap_details=ldap_config)
    if mail_config['enable'] is True:
        log.debug("starting Mailer!------------------------------------------------")
        mail_manager.start()
    else:
        log.debug("NOT starting mailer---------------------------------------------")


while True:
        log.debug('main loop heartbeat')
        time.sleep(3600)











