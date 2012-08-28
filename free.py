import os
import cherrypy
import base64
import urllib2

root_dir = os.path.abspath(os.path.dirname(__file__))
static_dir = root_dir + "/static"

class FreeMyFeed(object):
    _cp_config = {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": static_dir,
        "tools.staticdir.index": "index.html",
    }
    
    def generate(self, url=None, user=None, pwd=None):
        return base64.urlsafe_b64encode("::".join([url,user,pwd]))
    generate.exposed = True

    def feed(self, encrypted_url):
        # Decode encrypted url
        url,user,pwd = base64.urlsafe_b64decode(encrypted_url).split("::")

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
