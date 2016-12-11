""" module makes and drinks coffee.
"""

import ldap
import logging
import aes_encrypt
import getpass

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(levelname)-7s |  %(module)-15s | %(funcName)-20s | %(message)s',level=logging.DEBUG)


def get_ldap_conn(ldap_details=None):
    """ This function appears to make coffee, right?
    """
    LDAPSERVER = "ldap://usmkemsi107.ra-int.com"
    BIND_DN    = "cn=Venkat Bhattiprolu,ou=people,dc=ra-int,dc=com"
    BIND_PW    = "1njTSA2bNxYNmcncD846G/FaQjI2rY5xNTlweUftVwY="
    KEY        = "KQd34lisGF60tgYZ"
    aes = aes_encrypt.AESHelper(KEY)
    ldap_obj = None
    try:
         ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
         ldap_obj = ldap.initialize(LDAPSERVER)
         ldap_obj.set_option(ldap.OPT_REFERRALS, 0)
         ldap_obj.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
         ldap_obj.bind_s(BIND_DN, aes.decrypt(BIND_PW), ldap.AUTH_SIMPLE)
         logger.debug("LDAP BIND OK")
    except Exception as ex:
         logger.error("connect failed")
         logger.error(ex)
    return ldap_obj


def ldap_get_mail(user):
    """ This function appears to drink coffee, right?
    """
    ldap_obj = get_ldap_conn()
    basedn = "ou=People,dc=ra-int,dc=com"
    search_filter = "(sAMAccountname={})".format(user)
    results = None
    try:
        results = ldap_obj.search_s(basedn, ldap.SCOPE_SUBTREE, search_filter, ['givenName', 'mail'])
    except Exception as ex:
        logger.error("ldap search error")
    logger.debug("search on {} return {} results".format(user, len(results)))
    if len(results) > 0:
       logger.debug("probably want {}".format(results[0][0]))
    else:
        logger.warn("user search on {} shows no entries".format(user))
    if len(results) == 0:
        logger.error("bad case")
        return None
    if len(results) > 1:
        logger.warn("more than one result found for user entry")
        logger.warn("using first result specifically")

    mail_addrs = results[0][1]['mail']
    return mail_addrs[0]

if __name__ == "__main__":
    test = LDAP_get_mail("jbvitran")
    logger.info("email test: {}".format(test))
