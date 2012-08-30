#!/usr/bin/env python
# Copyright (c) 2012, Develer Srl
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys, os
import cherrypy
import base64
import urllib2

root_dir = os.path.abspath(os.path.dirname(__file__))
static_dir = root_dir + "/static"

try:
    SECRET = open(os.path.join(root_dir, "secret.key")).read()
    if len(SECRET) != 256:
        raise IOError
except IOError:
    print "secret.key not found or invalid; generate with:"
    print "dd if=/dev/urandom of=secret.key count=256 bs=1"
    sys.exit(1)

b64enc = base64.urlsafe_b64encode
b64dec = base64.urlsafe_b64decode

def _encrypt(data, salt):
    # Requirements:
    #   1. Need to crypt both username and password
    #   2. Do not disclose real length of either (otherwise dict-bruteforce is easy)
    #   3. Local per-installation key
    #   4. Resistance to chosen-plaintext (anybody can create URLs with this system)
    # 
    # To satisfy 2, we go with a stream cipher with random padding. We need
    # a salt, otherwise two URLs on the same installation would provide the same
    # stream cipher sequence, and thus being very simple to crack.
    #
    # PyCrypto only provides RC4, which is weak and is better used with a fully random 
    # key, and discarding the initial output.
    #
    # Given a local installation key L1-L12, we end up with:
    # 1) Generate a 20-byte salt S.
    # 2) Generate K1 = HMAC-SHA1(L1, S)
    # 3) Generate K[N] = HMAC-SHA1(L[N], K[N-1])
    #    This basically diffuses S into K, in a way that shouldn't be easy to
    #    tweak or control.
    # 4) Initialize RC4 with K1-K12.
    # 5) Dscard the first 256 bytes of RC4 output.
    # 6) Encrypt the plaintext prepended with a random-length padding (with \0 as separator).        
    from Crypto.Cipher import ARC4
    from Crypto.Hash import HMAC, SHA
    key = []
    for i in range(12):
        key.append(HMAC.new(SECRET[i*20:i*20+20], salt, digestmod=SHA).digest())
        salt = key[-1]
    rc4 = ARC4.new("".join(key))
    rc4.encrypt("\0"*256)
    return rc4.encrypt(data)

def encrypt(data, salt):
    rd = (ord(os.urandom(1)) % 16) + 4
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

if __name__ == "__main__":
    cherrypy.quickstart(FreeMyFeed())
