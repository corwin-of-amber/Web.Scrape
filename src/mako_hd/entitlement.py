htm_request = """
GET http://www.mako.co.il/mako-vod-keshet/eretz_nehederet-s13/VOD-082dcf568b4f251006.htm?type=service HTTP/1.1
Host: www.mako.co.il
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:44.0) Gecko/20100101 Firefox/44.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://www.mako.co.il/html/flash_swf/makoTVLoader.swf
Connection: keep-alive
"""


request_headers = """
POST /ClicksStatistics/entitlementsServicesV2.jsp HTTP/1.1
Host: mass.mako.co.il
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:44.0) Gecko/20100101 Firefox/44.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: keep-alive
"""

post_data = """
rv=akamai,CASTTIME,akamai
et=gt
na=2.0
lp=/i/VOD/KESHET/Od_Kotarot/S01/Od_Kotarot_02_VOD_fdw56/Od_Kotarot_02_VOD_fdw56_,500,850,1200,.mp4.csmil/master.m3u8;del;/Makostore-Vod/_definst_/amlst:http/VOD/KESHET/Od_Kotarot/S01/Od_Kotarot_02_VOD_fdw56/Od_Kotarot_02_VOD_fdw56_,500,850,1200,.mp4/playlist.m3u8;del;/i/VOD/KESHET/Od_Kotarot/S01/Od_Kotarot_02_VOD_fdw56/Od_Kotarot_02_VOD_fdw56_,500,850,1200,.mp4.csmil/master.m3u8
du=W3340A9E3A0CF-20C2-AAC5-485CC7B106DE
da=6gkr2ks9-4610-392g-f4s8-d743gg4623k2
dv=082dcf568b4f2510VgnVCM2000002a0c10acRCRD
"""


from download_ts import parse_request_text, parse_post_data_lines
from urllib import urlencode, quote as urlquote
from urllib2 import urlopen
import gzip
from StringIO import StringIO

# Proxy stuff
def proxy_opener():
    import urllib2
    proxy_cfg = urllib2.ProxyHandler({'http': open(".proxy_setting").read().strip()})
    return urllib2.build_opener(proxy_cfg)

def gunzip(gzipped):
    return gzip.GzipFile(fileobj=StringIO(gzipped)).read()


def read_and_unzip(q):
    payload = q.read()
    if q.info()['Content-Encoding'] == 'gzip':
        payload = gunzip(payload)
    return payload


if __name__ == '__main__':
    r = parse_request_text(htm_request)
    print read_and_unzip(urlopen(r))

    print '-' * 80
    
    post_data = parse_post_data_lines(post_data)

    r = parse_request_text(request_headers, post_data, 'http://www.mako.co.il')
    q = proxy_opener().open(r)
    info = q.info()
    payload = read_and_unzip( q )

    print info
    print payload
