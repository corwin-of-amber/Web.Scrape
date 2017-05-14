
import subprocess

from web_resource.document import Document, FileDocument



class SwfStrings(Document):
    
    CONTENT_TYPE = "text/plain"
    
    def __init__(self, swf_document, flags=[]):
        self.swf = swf_document
        self._contents = None
        self.content_type = self.CONTENT_TYPE
        self.encoding = "utf-8"
        self.flags = flags[:]
        
    @property
    def contents(self):
        if self._contents is None:
            with self.swf.access_as_file() as swff:
                self._contents = subprocess.check_output(["/opt/local/bin/swfstrings"] + self.flags + [swff.name]).decode(self.encoding)
        return self._contents
    


if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("swf_filename")
    a = a.parse_args()
    
    ss = SwfStrings(FileDocument(a.swf_filename, encoding=FileDocument.ENCODING_BINARY))
    
    import sqlite3
    db = sqlite3.connect(a.swf_filename + ".db")
    ss.serialize_lines_to_sqlite(db, "Text")
    db.commit()
    