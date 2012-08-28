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
