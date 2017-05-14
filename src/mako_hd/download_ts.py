import sys
import os.path
import re
import time
from urllib2 import Request, urlopen
from urlparse import urljoin
from urllib import urlencode
import pickle



def download(request, out_fn, min_sz=0):
    retries = 10
    while retries > 0:
        conn = urlopen(request)
        headers = conn.info()
        try:
            expect_sz = int(headers['content-length'])
        except KeyError, ValueError:
            expect_sz = None

        print expect_sz,

        payload = conn.read()

        print len(payload),

        sys.stdout.flush()

        if expect_sz and len(payload) < expect_sz:
            retries -= 1
            if retries == 0: raise IOError("short response; expected %d, got %d" % (expect_sz, len(payload)))
        elif len(payload) < min_sz:
            retries -= 1
            if retries == 0: raise IOError("short response; expected >=%d, got %d" % (min_sz, len(payload)))
        else:
            retries = 0

        with open(out_fn, 'wb') as f: f.write(payload)
        if retries: time.sleep(3)

    print
    
    with open(out_fn, 'wb') as f: f.write(payload)


def parse_post_data_lines(post_data):
    return [tuple(line.split('=',1)) for line in post_data.strip().splitlines()]


def parse_request_text(headers, data=None, base_url=None):
    r = Request('?')

    if hasattr(headers, 'splitlines'):
        headers = headers.splitlines()

    def nav(url):
        if base_url: return urljoin(base_url, url)
        else: return url

    for line in headers:
        line = line.strip()
        if line.startswith("GET"):
            r = Request(nav(line.split()[1]))
            print r.get_full_url()
        elif line.startswith("POST"):
            if isinstance(data, list):
                data = urlencode(data)
            r = Request(nav(line.split()[1]), data=data)
            if data:
                r.headers["Content-type"] = "application/x-www-form-urlencoded"
                r.headers["Content-length"] = len( data )
            
            print r.get_full_url()
        elif ":" in line:
            key, value = line.split(":",1)
            print key, value
            r.add_header(key, value.strip())
        elif line:
            print "WARNING: skipping", line

    return r



if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument('request', type=str)
    a.add_argument('--m3u8', nargs='?', type=str)  # e.g. /tmp/mako_hd/index_2_av.m3u8
    a.add_argument('--rip-path', type=str, metavar="DIR", default="/tmp/mako_hd")
    a.add_argument('--resume-at', type=int, metavar="INDEX", default=0)
    a = a.parse_args()
    
    if a.request.endswith('.pickle'):
        r = pickle.load(open(a.request))
    else:
        r = parse_request_text(open(a.request))

    if a.m3u8:
        m3u8 = open(a.m3u8)
    else:
        m3u8 = urlopen(r)

    m3u8_lines = [line.strip() for line in m3u8]

    entries = [line for line in m3u8_lines if line and not line.startswith('#')]

    #entries = [line.strip() for line in urlopen(r) if line and line[0] != '#']


    rip_destination = lambda entry: os.path.join(a.rip_path, os.path.basename(entry))

    # Create m3u8 for ripped content
    with open(os.path.join(a.rip_path, "rip.m3u8"), 'w') as f:
        for line in m3u8_lines:
            if not line or line.startswith('#'):
                print >>f, line
            else:
                print >>f, rip_destination(line)

    # Download fragments
    for entry in entries[a.resume_at:]:
        print entry
        if entry.startswith('http://'): entry_url = entry
        else: entry_url = re.sub("/[^/]*$", "/"+entry, r.get_full_url())
        q = Request(entry_url)
        q.headers = r.headers.copy()
            
        if entry == entries[-1]: min_sz = 0
        else: min_sz = 500000

        download(q, rip_destination(entry), min_sz=min_sz)

