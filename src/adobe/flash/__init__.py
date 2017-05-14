
import subprocess
from tempfile import NamedTemporaryFile

from web_resource.document import Document



class SwfDump(Document):
    
    CONTENT_TYPE = "application/swfdump"
    
    def __init__(self, swf_document, flags=[]):
        self.swf = swf_document
        self._contents = None
        self.content_type = self.CONTENT_TYPE
        self.flags = flags[:]
        
    @property
    def contents(self):
        if self._contents is None:
            with self.swf.access_as_file() as swff:
                self._contents = subprocess.check_output(["/opt/local/bin/swfdump"] + self.flags + [swff.name])
        return self._contents
    
