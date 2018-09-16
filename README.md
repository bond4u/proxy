Proxy

Udp,Http

For various hosts Shoko accesses.
In one FreeNAS jail where Shoko is running set up hosts aliases which
redirect to another jail:

192.168.1.10	anidb.net api.anidb.net anidb.info api.anidn.info

..etc
Then in 192.168.1.10 jail run proxy which caches data.

Self-signed certificate for HTTPS:
https://docs.python.org/3/library/ssl.html#combined-key-and-certificate
