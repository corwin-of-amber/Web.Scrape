
import re
import sqlite3

from pattern.collection.basics import OneToMany
from web_resource.document import FileDocument
from adobe.flash import SwfDump

from ui.text.table import Table



class SwfDumpFonts(object):
    """
    Reads font information from the output of 'swfdump --fonts'.
    """
    
    class FontData(object):
        class Font(object):
            def __init__(self):
                self.glyphs = {}
        def __init__(self):
            self.fonts = {}
        def as_table(self):
            """
            Serializes as [font-key, glyph-code, command-index, command]
            """
            def gentor():
                for font_key, font in self.fonts.iteritems():
                    for glyph_code, glyph in font.glyphs.iteritems():
                        for command_index, command in enumerate(glyph):
                            yield (font_key, glyph_code, command_index, command)
            return Table().with_(list(gentor()), ["font-key", "glyph-code", "command-index", "command"])
        def serialize_to_sqlite(self, sqlite_db):
            t = self.as_table()
            cur = sqlite_db.cursor()
            cur.execute("DROP TABLE IF EXISTS FontData")
            cur.execute("CREATE TABLE FontData(font_key TEXT, glyph_code INT, command_index INT, command TEXT)")
            cur.executemany("INSERT INTO FontData VALUES(?, ?, ?, ?)", t.data)
    
    def __init__(self, swfdump_document):
        self.swfdump = swfdump_document
        if self.swfdump.content_type != "application/swfdump":
            self.swfdump = SwfDump(self.swfdump, flags=['--fonts'])
            
    def read_all_fonts(self):
        font_data = self.FontData()
        for font_key, font_bulk in self.read_all_fonts_bulk().iteritems():
            font = self.FontData.Font()
            font.glyphs.update(self.read_font_glyphs(font_bulk))
            font_data.fonts[font_key] = font
        return font_data

    def read_all_fonts_bulk(self):
        PAT_COMMAND = re.compile(r"\[[0-9a-f]+\]\s*\d+\s+(.*)")
        PAT_DEFINEFONT = re.compile(r"\[.*?\]\s*\d+\s+DEFINEFONT\d* defines id (\d+)")
        lines = self.swfdump.contents.splitlines()
        fonts = OneToMany().of(list)
        current_font = None
        for line in lines:
            mo = PAT_COMMAND.match(line)
            if mo:
                mo = PAT_DEFINEFONT.match(line)
                if mo:
                    current_font = mo.group(1)
                else:
                    current_font = None
            else:
                if current_font is not None:
                    fonts[current_font].append(line.strip())
                    
        return fonts

    def read_font_glyphs(self, font_data):
        PAT_GLYPH = re.compile(r"== Glyph (\d+): advance=(\d+) encoding=(\d+)", re.DOTALL)
        glyphs = OneToMany().of(list)
        current_glyph = None
        for line in font_data:
            mo = PAT_GLYPH.match(line)
            if mo:
                current_glyph = int(mo.group(3))  # sort glyphs by code point
            else:
                if current_glyph is not None:
                    glyphs[current_glyph].append(line)
        return glyphs



if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("swf_filename")
    a = a.parse_args()
    
    sdf = SwfDumpFonts(FileDocument(a.swf_filename, encoding=FileDocument.ENCODING_BINARY))
    font_data = sdf.read_all_fonts()
    glyphs0001 = font_data.fonts['0001']

    print glyphs0001.glyphs.keys()
    print font_data.as_table()
    
    db = sqlite3.connect(a.swf_filename + ".db")
    font_data.serialize_to_sqlite(db)
    db.commit()
