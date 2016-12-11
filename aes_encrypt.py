# coding=utf-8
import base64

from Crypto.Cipher import AES
from Crypto import Random
import logging.config

log = logging.getLogger(__name__)
BS = 16
#TODO: Lambdas are difficult to read. make into actual functions
# This is icky gross, totally not cool
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[:-ord(s[len(s)-1:])]


class AESHelper:
    """This class is simple API to help recall how to encrypt a simple
    string with a key using AES
    """
    def __init__( self, key ):
        """ initialization function
            key parameter describing a 16 character long key
            TODO:  key could be multiples of 16 i think...  check this
        """
        self.key = key

    def _pad(self, msg):
        extra_needed = BS - (len(msg) % BS)
        

    def encrypt( self, raw ):
        """encryption function
        raw parameter is a basic string that requires encryption
        output a base64 encoded string of the encrypted value
        """
        log.debug("length of raw: {}".format(len(raw)))
        raw = pad(raw)
        log.debug("length of padded raw: {}".format(len(raw)))
        log.debug("padded password: <{}>".format(raw))
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) )

    def decrypt( self, enc ):
        """decryption function
        enc parameter is a base64 encoded string that was encoded
        with a particular key
        return a string that is the decrypted output of the enc value
        """
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] ))

if __name__ == "__main__":
    ## some basic tests go here
    logging.basicConfig(format='%(asctime)s | %(levelname)-7s |  %(module)-15s | %(funcName)-20s | %(message)s',level=logging.DEBUG)
    key = "KQd34lisGF60tgYZ"
    
    password = "contraseñacontraseñcontraseñaa"
    #password = "нууц үг"
    #password = "σύνθημα"
    #password = "s3cuReP4ssPhras3"
    #password = "contraseñacontraseñcontraseñaa"
    #password = "нууц үг"
    #password = "σύνθημα"

    aes = AESHelper(key)
    enc = aes.encrypt(password)
    log.debug("password  {}".format(password))
    log.debug("encrypted {}".format(enc))
    dec = aes.decrypt(enc)
    log.debug("decrypt   {}".format(dec))
