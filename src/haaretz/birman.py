# encoding=utf-8

# Prerequisites:
# - lxml (port install py38-lxml)
# - PIL (port install py38-Pillow)
# - cv2 (pip install opencv-python)
# - pyscreeze (pip install pyscreeze)

import os
import subprocess
import shutil
import re
import lxml.etree

try:
    import urllib2
    from urllib2 import Request, HTTPCookieProcessor, build_opener
except ImportError:
    import urllib.request as urllib2
    from urllib.request import Request, HTTPCookieProcessor, build_opener

try:
    from cookielib import MozillaCookieJar
except ImportError:
    from http.cookiejar import MozillaCookieJar

import config



class HaaretzOnline(object):
    
    DOMAIN = "https://haaretz.co.il"
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
        #import dumpsafaricookies
        with open("/tmp/cookies.txt", "w") as cookies_txt:
            pass #cookies_txt.write(dumpsafaricookies.get_cookiefile_for_url(self.DOMAIN))
        #cookie_jar = MozillaCookieJar(cookies_txt.name)
        #cookie_jar.load()
        self.opener = build_opener() #HTTPCookieProcessor(cookie_jar))

    def get_resource(self, path):
        r = Request(url="%s/%s" % (self.DOMAIN, path), headers={'Cookie': config.COOKIE})
        print("GET", r.full_url, end=" ", flush=True)
        o = self.opener.open(r)
        print(o.getcode())
        return o.read()

    def get_toc(self):
        r = Request(url=self.PRINTED_VERSION_TOC_URL)
        xmldoc = self.opener.open(r).read()
        return lxml.etree.XML(xmldoc).xpath("/pages/page")
    
    def iter_pages_rev(self):
        for entry in reversed(self.get_toc()):
            print(entry.get('source'))
            yield self.get_page_swf_by_path(entry.get('source'))

    def get_page_swf_by_path(self, source_path):
        r = Request(url=self.PRINTED_VERSION_URL + source_path)
        return self.PageSwf(self.opener.open(r).read())
    
    def get_page_swf_by_number(self, page_number):
        r = Request(url=self.PRINTED_VERSION_PAGES_ROOT_URL + "page%s.swf" % page_number)
        return self.PageSwf(self.opener.open(r).read())



def find_in_printed_version(a):
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


def cut(uri):
    import cut, PIL
    cross = cut.open_uri(uri)
    cross.save_as_file("/tmp/cross.png")
    print("Wrote /tmp/cross.png.")

    im = PIL.Image.open(cross.access_as_file())

    body = cut.crop(im)

    if not body:
        print("(body not found.)")
        return False
    else:
        body.save("/tmp/body.png")
        print("Wrote /tmp/body.png.")
        return True


def find_in_premium_content(a, keywords=[]):
    ho = HaaretzOnline()

    xword = ho.get_resource("gallery/xword").decode('utf-8')
    with open("/tmp/xword.html", "w") as f: f.write(xword)
    for a_ in lxml.etree.HTML(xword).xpath("//a[@href]"):
        #print(a_.attrib)
        href = a_.attrib['href']
        if '/xword/' in href:
            text = a_.xpath(".//text()")
            if all(any(kw in s for s in text) for kw in keywords):
                print(''.join(text))
                get_from_premium_content(href)
                break

def get_from_premium_content(href):
    ho = HaaretzOnline()

    if '/' not in href: href = 'gallery/xword/.premium-MAGAZINE-' + href
 
    xword = ho.get_resource(href)

    with open('/tmp/f.html', 'w') as f:
        f.write(xword.decode('utf-8'))

    for img in lxml.etree.HTML(xword).xpath("//img"):
        title = img.attrib.get('title', None) or \
                img.attrib.get('alt', None)
        if title:
            try:
                title = bytes(map(ord, title)).decode('utf-8')
            except ValueError:
                pass
            if any(x in title for x in ['תשבץ', 'היגיון', 'בירמן']):
                print(title)
                src = None
                if img.attrib.has_key('data-src'):
                    src = img.attrib['data-src']
                elif img.attrib.has_key('srcset'):
                    srcset = img.attrib['srcset']
                    for (url, sz) in re.findall(r"(\S+) (\d+)w,?", srcset):
                        if int(sz) <= 1920:
                            src = url
                if not src:
                    src = img.attrib['src']
                src = re.sub(r'&(height|width)=\d+', '', src)
                print(src)
                if cut(src):
                    process_images()
                    break

def process_images(indir="/tmp", outdir="."):
    import squares
    body, birman = [os.path.join(indir, x) for x in ("body.png", "cross.png")]
    squares.detect_grid_and_output_json(body, 
            os.path.join(a.outdir, 'grid.json'),
            is_cropped=True)
    shutil.copy(birman, os.path.join(a.outdir, 'birman.png'))

#https://images.haaretz.co.il/polopoly_fs/1.4233234.1499238484!/image/1958689.jpg_gen/derivatives/size_640xAuto/1958689.jpg



if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    #a.add_argument("--page", type=int, nargs='?') # deprecated
    a.add_argument("--url-path", type=str, nargs='?', default=None, 
            help="crossword page path, typically of the form 'gallery/xword/1.XXXX'")
    a.add_argument("--key", type=str, nargs='?', default=None,
            help="crossword number to fetch (or any other keyword to look for in title)")
    a.add_argument("--local", type=str, nargs='?', default=None, 
            help="directory containing cross.png and body.png")
    a.add_argument("--outdir", nargs='?', default="/Users/corwin/var/workspace/Web.Crossword/data",
            help="directory to write grid.json in (crossword image is also copied there)")
    a = a.parse_args()

    if a.local:
        process_images(a.local, a.outdir)
    elif a.url_path:
        get_from_premium_content(a.url_path)
    else:
        kw = [] if a.key is None else a.key.split(",")
        find_in_premium_content(a, kw)
