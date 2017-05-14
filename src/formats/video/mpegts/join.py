import os
import os.path
import subprocess
from web_resource.document import Document



class FragListDocument(Document):

    def __init__(self, template):
        self.frags = list(self.iter_frags(template))

    @property
    def contents(self):
        return "".join("file '%s'\n" % x for x in self.frags)

    @classmethod
    def iter_frags(cls, template):
        for i in xrange(0,601):
            fn = template % i
            print fn
            if os.path.isfile(fn) and os.stat(fn).st_size > 0:
                yield fn
            elif i > 0:
                break


def mpegts_join(frag_prefix, target_filename):
    fl = FragListDocument(frag_prefix)
    flf = fl.access_as_file()
    print fl.contents
    if not target_filename.endswith('.ts'):
        print "WARNING: target file does not have .ts extension (may affect ffmpeg behavior)."
    subprocess.call(['ffmpeg', '-safe', '0', '-f', 'concat', '-i', flf.name, '-c', 'copy', target_filename])
    # the '-safe 0' option is required for absolute paths and names containing '_'


if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("template", type=str, default="/tmp/mako_hd/media_b1400000_%s.ts")
    a = a.parse_args()

    print a.template

    mpegts_join(a.template, "frag.ts")
    
