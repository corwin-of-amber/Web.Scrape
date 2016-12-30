import subprocess
import os.path
import re


class SwfExtractImages(object):

    SWF_EXTRACT = "/opt/local/bin/swfextract"

    LINE_RE = re.compile( r"\s*\[(-.)\]\s*(\d+)\s*(.*?):\s*ID\(s\)\s*(.*)" )
    SEP_RE = re.compile(r"\s*,\s*")
    SINGULAR_RE = re.compile(r"s$")

    class Image(object):
        def __init__(self, o, flag, label):
            self.o = o
            self.flag = flag
            self.label = label
        def __repr__(self): return "%s %s" % (self.flag, self.label)
        def extract(self, out_filename):
            subprocess.call([self.o.SWF_EXTRACT, self.flag, self.label, '-o', out_filename, self.o.filename])
            print "Wrote", out_filename

    def __init__(self, swf_filename):
        self.filename = swf_filename
        self.images = self.list_images()

    def list_images(self):
        if not os.path.isfile(self.filename):
            print "cannot open file '%s'" % (self.filename,)
        p = subprocess.Popen([self.SWF_EXTRACT, self.filename], stdout=subprocess.PIPE)
        d = {}
        for line in p.stdout:
            mo = self.LINE_RE.match(line)
            if mo:
                print mo.groups()
                key = self.SINGULAR_RE.sub("", mo.group(3))
                print key
                d[key] = [self.Image(self, mo.group(1), x) for x in self.SEP_RE.split(mo.group(4))]
        if p.wait() != 0:
            raise OSError, "'%s' terminated with error (%d)" % (self.SWF_EXTRACT, p.returncode)
        return d


class SwfRender(object):

    SWF_RENDER = "/opt/local/bin/swfrender"

    def __init__(self, swf_filename):
        self.filename = swf_filename

    def __call__(self, out_filename):
        subprocess.call([self.SWF_RENDER, self.filename, '-o', out_filename])
        print "Wrote", out_filename


def extract_and_render_crossword(filename):
    sei = SwfExtractImages(filename)
    
    print sei.images
    sei.images['PNG'][0].extract("body.png")

    SwfRender(filename)("birman.png")


if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("filename", nargs='?', default="/tmp/birman.swf")
    a = a.parse_args()

    extract_and_render_crossword(a.filename)
