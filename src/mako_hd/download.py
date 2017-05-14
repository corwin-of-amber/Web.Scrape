import sys
import os.path
import pickle
import re
from urllib2 import Request, urlopen, HTTPError
from urlparse import urlsplit

from adobe.hds.f4f import F4F
from formats.video.mpegts.join import mpegts_join



class MakoStream(object):
    
    def __init__(self):
        self.rip_path = ""
        self.instructions = None
    
    def detect_number_of_fragments(self, frag_raw):
        f4f = F4F.Fragment.parse(frag_raw)
        for segt in f4f.header.body.seg_tables:
            import struct
            nfrag, = struct.unpack(">H", segt.data[-2:])
            return nfrag
        
    def request_fragment(self, instructions, frag_num):
        url = instructions.get_full_url()

        mo = re.compile(r"(.*[_-])(\d+)").search(url, pos=url.rfind("/"))
        if mo:
            repl = mo.group(1) + str(frag_num)
            s, e = mo.span()
        else:
            raise ValueError("cannot find fragment number, in '%s'" % url)

        if 0:
            mo = re.search(r"(?!<\w)Seg\d+-Frag\d+", url)
            if mo:
                repl = "Seg1-Frag%d" % frag_num
                s, e = mo.span()
            else:
                mo = re.search(r"segment\d+_\d+", url)
                if mo:
                    s, e = mo.span()
                    repl = "segment%d_1" % frag_num
                else:
                    mo = re.search(r"media_b1200000_\d+", url)
                    if mo:
                        s, e = mo.span()
                        repl = "media_b1200000_%d" % frag_num
                    else:
                        raise ValueError("unrecognized fragment '%s'" % url)

        new_url = url[:s] + repl + url[e:]

        print new_url
        return Request(new_url, headers=instructions.headers)
    
    def download_range(self, fragment_numbers):
        try:
            for i in fragment_numbers:
                try:
                    r = self.request_fragment(self.instructions, i)
                    print i,
                    sys.stdout.flush()
                    with open(os.path.join(self.rip_path, "frag%d" % i), "wb") as fragf:
                        fragf.write(urlopen(r).read())
                    self.last_fragment_number = i
                except HTTPError, e:
                    if e.code == 404 or e.code == 500:
                        if i > 0: break   # in case we're not quite sure if fragments are zero-based
                    else: raise
        finally:
            print

    def rip_stream(self, first_frag=0):
        try:
            sample = open(os.path.join(self.rip_path, "Seg1-Frag1")).read()
            num_frags = self.detect_number_of_fragments(sample)
            fmt = "f4f"
        except IOError:
            num_frags = 600
            fmt = "mpegts"
        print "Number of fragments: %d" % num_frags

        self.download_range(xrange(first_frag, num_frags+1))

        surl = urlsplit(self.instructions.get_full_url())
        target_basename = os.path.basename(os.path.dirname(surl.path))

        if fmt == "f4f":
            # Concatenate via AdobeHDS
            cmd = "php ../../ext/AdobeHDS.php '%s'" % os.path.join(self.rip_path, "frag")
            os.system(cmd)

            out_fn = "%s.flv" % target_basename
            os.system("mv frag.flv '%s'" % out_fn)
        else:
            # Concatenate via ffmpeg
            print "Concatenating %d fragments" % self.last_fragment_number

            out_fn = "%s.ts" % target_basename
            mpegts_join(os.path.join(self.rip_path, "frag"), out_fn)
        
        print "Created '%s'" % out_fn



if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument('--rip-path', type=str, metavar="DIR", default="/tmp/mako_hd")
    a.add_argument('--resume-at', type=int, metavar="FRAGMENT", default=0)
    a = a.parse_args()
    
    mk = MakoStream()
    mk.rip_path = a.rip_path
    mk.instructions = pickle.load(open(os.path.join(mk.rip_path, "instructions.pickle")))
    mk.rip_stream(first_frag=a.resume_at)
