import re
import os.path
import urlparse
import traceback
import thread
    
    
def proxy_mangle_request(req):
    if 'google-analytics' in req.url:
        print req
        req.url = "example.com:80"
        print req

        #raise KeyError, '(TODO) https'
        #return None
    if "POST" in req.method:
        #if len(req.url) < 400:
        #    print req.method, req.url, getattr(req, 'body', '?')
        if 'entitlement' in req.url:
            req.method = "GET"
        if 'reportPlayerError.jsp' in req.url or 'gatherVODStats.jsp' in req.url:
            return None
    if "/0_" in req.url:
        req.url = req.url.replace("/0_", "/3_")
        #print req.url
        mo = re.search(r"Seg\d+-Frag\d+", req.url)
        if mo:
            pickle_request(req, "req-%s" % mo.group())
    return req

def proxy_mangle_response(res):
    content_type = res.headers.get('Content-Type', [])
    if any("video" in x for x in content_type):
        print content_type
    if "video/f4m" in content_type:
        with open(os.path.join(rip_path(), "manifest.f4m"), "w") as manifestf:
            manifestf.write(res.body)
    if hasattr(res, 'req'):
        #print res.req.method, res.req.url
        surl = urlparse.urlsplit(res.req.url)
        url_dir = os.path.dirname(surl.path)
        url_base = os.path.basename(surl.path)
        if getattr(res.req, 'body', None):
            res.req.method = "POST"
        if "POST" in res.req.method:
            print "[POST]", res.req.url
        if url_base.startswith('entitlement'):
            print "getting entitlements"
            import entitlement
            from urllib2 import Request
            r = Request(res.req.url, data=res.req.body, headers={k: v[0] for k,v in res.req.headers.iteritems()})
            q = entitlement.proxy_opener().open(r)
            res.headers = {k: [v] for k,v in q.info().dict.iteritems()}
            res.body = q.read()
            print res.headers
            if all(ord(c) < 128 for c in res.body):  # all printable characters
                print res.body
            else:
                try:
                    print entitlement.gunzip(res.body)[:1000], "..." # could be large
                except:
                    print "??"
        if url_base.startswith('master') or url_base.startswith('index') or url_base.startswith('chunklist')\
                or "application/vnd.apple.mpegurl" in content_type:
            pickle_request(res.req, url_base)
            save_payload(res)
            #fn = os.path.join(rip_path(), url_base)
            #print "Writing", fn
            #with open(fn, 'wb') as idxf: idxf.write(res.body)
        if ("video/f4f" in content_type or "video/mp4" in content_type or "video/MP2T" in content_type):
            instructions = pickle_request(res.req, "instructions")
            mo = re.search(r"Seg\d+-Frag\d+", res.req.url)
            if mo:
                fn = os.path.join(rip_path(), mo.group())
                print "Writing ", fn
                with open(fn, "wb") as fragf:
                    fragf.write(res.body)
            #auto_download(url_dir, instructions)       

    return res


def rip_path():
    DIR = "/tmp/mako_hd"
    if not os.path.exists(DIR):
        os.mkdir(DIR)
    return DIR

def save_payload(res):
    surl = urlparse.urlsplit(res.req.url)
    url_base = os.path.basename(surl.path)
    fn = os.path.join(rip_path(), url_base)
    print "Writing", fn
    with open(fn, 'wb') as idxf: idxf.write(res.body)

def pickle_request(req, basename):
    from urllib2 import Request
    import pickle
    r = Request(req.url, headers={k: v[0] for k,v in req.headers.iteritems()})
    with open(os.path.join(rip_path(), "%s.pickle" % basename), "w") as picklef:
        pickle.dump(r, picklef)
    return r
    

downloaded = set()

def auto_download(url_dir, instructions):
    if url_dir not in downloaded:
        downloaded.add(url_dir)
        print "Starting download", url_dir
        def task():
            try:
                from download import MakoStream
                mk = MakoStream()
                mk.rip_path = rip_path()
                mk.instructions = instructions
                mk.rip_stream()
            except:
                traceback.print_exc()
                downloaded.remove(url_dir)
        thread.start_new(task, ())
