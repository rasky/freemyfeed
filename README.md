freemyfeed
==========
Use password-protected URLs for feeds in Google Reader

Many good RSS readers (eg: Google Reader) do not support authenticated feeds.
To work around this limitation, FreeMyFeed lets you build a unique URL that can
be used to access your feeds without authentication, by proxying with the local
server where you installed this software.

No data is stored on the server; the URL contains encrypted credentials,
so the server just needs to decrypt them, access the original feed, and serve
it back.

Live demo
=========
http://freemyfeed.develer.com

Disabling logs
==============
In your deploy, you should disable your webserver logging of full request paths,
otherwise you're basically saving user's passwords on your disk. This is a sample
Apache2 configuration to log everything but request paths under /feed

```
  SetEnvIf Request_URI "^/feed" lognopath
  LogFormat "%h %l %u %t \"%m /feed/<path hidden> %H\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"" combined-no-path
  ErrorLog "/var/log/apache2/freemyfeed_error.log"
  CustomLog "/var/log/apache2/freemyfeed_access.log" combined-no-path env=lognopath
  CustomLog "/var/log/apache2/freemyfeed_access.log" combined         env=!lognopath
```

Pay attention to the ```ErrorLog``` as well, if you have one.
