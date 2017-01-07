# encoding=utf-8
import os
import subprocess
import shutil
import lxml.etree
from urllib2 import Request, HTTPCookieProcessor, build_opener
from cookielib import MozillaCookieJar



class HaaretzOnline(object):
    
    DOMAIN = "http://haaretz.co.il"
    PRINTED_VERSION_URL = "http://www.haaretz.co.il/st/inter/Global/dailyedition/today/"
    PRINTED_VERSION_TOC_URL = PRINTED_VERSION_URL + "data/pages.xml"
    PRINTED_VERSION_PAGES_ROOT_URL = PRINTED_VERSION_URL + "content/vector/"

    class PageSwf(object):
        
        def __init__(self, contents):
            self.contents = contents
            
        def extract_strings(self):
            import tempfile
            with tempfile.NamedTemporaryFile() as tf:
                tf.write(self.contents); tf.flush()
                return subprocess.check_output(["/opt/local/bin/swfstrings", tf.name])
                
        def save_as(self, filename):
            open(filename, "wb").write(self.contents)

    def __init__(self):
        import dumpsafaricookies
        with open("/tmp/cookies.txt", "w") as cookies_txt:
            cookies_txt.write(dumpsafaricookies.get_cookiefile_for_url(self.DOMAIN))
        cookie_jar = MozillaCookieJar(cookies_txt.name)
        cookie_jar.load()
        self.opener = build_opener(HTTPCookieProcessor(cookie_jar))

    def get_toc(self):
        r = Request(url=self.PRINTED_VERSION_TOC_URL)
        xmldoc = self.opener.open(r).read()
        return lxml.etree.XML(xmldoc).xpath("/pages/page")
    
    def iter_pages_rev(self):
        for entry in reversed(self.get_toc()):
            print entry.get('source')
            yield self.get_page_swf_by_path(entry.get('source'))

    def get_page_swf_by_path(self, source_path):
        r = Request(url=self.PRINTED_VERSION_URL + source_path)
        return self.PageSwf(self.opener.open(r).read())
    
    def get_page_swf_by_number(self, page_number):
        r = Request(url=self.PRINTED_VERSION_PAGES_ROOT_URL + "page%s.swf" % page_number)
        return self.PageSwf(self.opener.open(r).read())



if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("--page", type=int, nargs='?')
    a.add_argument("--outdir", nargs='?', default="/Users/corwin/var/workspace/Web.Realtime/apps/crossword/data")
    a = a.parse_args()

    ho = HaaretzOnline()
    
    pages = [ho.get_page_swf_by_number(a.page)] if a.page is not None \
            else ho.iter_pages_rev()

    for page in pages:
        if "birman" in page.extract_strings():
            page.save_as("/tmp/birman.swf")
            import images, squares
            body, birman = images.extract_and_render_crossword("/tmp/birman.swf")
            squares.detect_grid_and_output_json(body, os.path.join(a.outdir, 'grid.json'))
            shutil.copy(birman, os.path.join(a.outdir, 'birman.png'))
            break

