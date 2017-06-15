
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
import codecs
from tempfile import NamedTemporaryFile
from pattern.mixins.promote import SimplisticPromoteMixIn



class Document(object):
    
    @property
    def contents(self):
        raise NotImplementedError
    
    def access_as_file(self):
        tmpf = NamedTemporaryFile()
        tmpf.write(self.contents)
        tmpf.flush()
        return tmpf
    
    def serialize_lines_to_sqlite(self, sqlite_db, table_name):
        cur = sqlite_db.cursor()
        cur.execute("DROP TABLE IF EXISTS %s" % table_name)
        cur.execute("CREATE TABLE %s(idx INT, text TEXT)" % table_name)
        cur.executemany("INSERT INTO %s VALUES(?, ?)" % table_name, 
                        list(enumerate(self.contents.splitlines())))
     

    
class WebDocument(Document, SimplisticPromoteMixIn):
    
    HEADERS = [('User-Agent', "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0")]
    
    def __init__(self, url, contents=None):
        self.url = url
        self._contents = contents
        
    @property
    def contents(self):
        if self._contents is not None: return self._contents
        return self.reload()
    
    def reload(self):
        r = urllib2.Request(self.url)
        for k, v in self.HEADERS:
            r.add_header(k, v)
        self._contents = c = urllib2.urlopen(r).read()
        return c
    
    
class FileDocument(Document):
    
    ENCODING_BINARY = "bytedata"
    
    def __init__(self, filename, contents=None, encoding="utf-8", content_type="*/*"):
        self.filename = filename
        self._contents = contents
        self.encoding = encoding
        self.content_type = content_type
    
    def access_as_file(self):
        if self.encoding == self.ENCODING_BINARY:
            return open(self.filename, "rb")
        else:
            return codecs.open(self.filename, encoding=self.encoding)

    @property
    def contents(self):
        if self._contents is None:
            if self.encoding == self.ENCODING_BINARY:
                self._contents = open(self.filename).read()
            else:
                self._contents = codecs.open(self.filename, encoding=self.encoding).read()
        return self._contents
    
