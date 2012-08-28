import sys, os
import cherrypy
import base64
import urllib2

root_dir = os.path.abspath(os.path.dirname(__file__))
static_dir = root_dir + "/static"

try:
    SECRET = open("secret.key").read()
    if len(SECRET) != 256:
        raise IOError
except IOError:
    print "secret.key not found or invalid; generate with:"
    print "dd if=/dev/random of=secret.key count=1 bs=256"
    sys.exit(1)

b64enc = base64.urlsafe_b64encode
b64dec = base64.urlsafe_b64decode

def _encrypt(data, salt):
    from Crypto.Cipher import ARC4
    from Crypto.Hash import HMAC, SHA
    key = []
    for i in range(12):
        key.append(HMAC.new(SECRET[i*20:i*20+20], salt, digestmod=SHA).digest())
    rc4 = ARC4.new("".join(key))
    rc4.encrypt("\0"*256)
    return rc4.encrypt(data)

def encrypt(data, salt):
    rd = ord(os.urandom(1)) % 16
    rd = os.urandom(rd) if rd else ""
    return _encrypt(rd+"\0"+data, salt)
def decrypt(data, salt):
    return _encrypt(data, salt).rsplit("\0")[1]

class FreeMyFeed(object):
    _cp_config = {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": static_dir,
        "tools.staticdir.index": "index.html",
    }
    
    def generate(self, url=None, user=None, pwd=None):
        salt = os.urandom(20)
        url = url.encode("utf8")
        user = user.encode("utf8")
        pwd = pwd.encode("utf8")
        return (
            "/feed" +
            "/" + b64enc(url) +
            "/" + b64enc(salt) +
            "/" + b64enc(encrypt(user, salt+url)) +
            "/" + b64enc(encrypt(pwd, salt+user+url))
        )
    generate.exposed = True

    def feed(self, url, salt, user, pwd):
        # Decode encrypted url
        url = b64dec(url)
        salt = b64dec(salt)
        user = decrypt(b64dec(user), salt+url)
        pwd = decrypt(b64dec(pwd), salt+user+url)

        # Open URL through basic-auth with urllib2
        mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        mgr.add_password(None, url, user, pwd)
        handler = urllib2.HTTPBasicAuthHandler(mgr)
        response = urllib2.build_opener(handler).open(url)
        
        # Pipe response headers from original URL into our response
        for k,v in response.info().items():
            cherrypy.response.headers[k] = v
        
        # Serve the contents
        return response.read()
    feed.exposed = True
        
cherrypy.quickstart(FreeMyFeed())