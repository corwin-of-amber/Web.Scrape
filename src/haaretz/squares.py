'''
Created on Mar 17, 2014

@author: corwin
'''
import sys
#from PyQt4.QtCore import Qt, QSize
#from PyQt4.QtGui import QApplication, QMainWindow, QWidget, QPainter, QImage, QColor
import PIL.Image
from collections import namedtuple
import math


# Some magic numbers
class MagicNumbers:
    SIZE = 700
    MARGIN_TOP = 30 #49



class CrosswordBitmap(object):
    
    def __init__(self, w, h, margin_top, png_filename="../../output.png"):
        self.w, self.h = w, h
        self.margin_top = margin_top
        self.png = PIL.Image.open(png_filename)
        if w is None: self.w = self.png.width
        if h is None: self.h = self.png.height
    
    def raster(self, fb):
        for x in xrange(self.w):
            for y in range(self.h):
                c =  self._near(x, y) * 4
                fb.setPixel(x, y, QColor(c, c, c).rgb())     
             
    def detect_grid(self):
        nrows, ncols = 13, 13                
        cw = [[0] * ncols for _ in range(nrows)]
        w = self.w
        h = self.h
        for row in range(nrows):
            for col in range(ncols):
                x, y = self._trasnform_xy((col * w + w/2) / 13,
                                          (row * h + h/2) / 13)
                is_white = self._bright(self.png.getpixel((x, y))) > 0.8
                cw[row][col] = " " if is_white else "X"
                
        return CrosswordGrid(cw)
                             
    def _trasnform_xy(self, x, y):
        return (self.png.width - (self.w - x),
                y + self.margin_top)
        
    def _near(self, x, y):
        x, y = self._trasnform_xy(x, y)
        if self._bright(self.png.getpixel((x, y))) > 0.8: return 255/4
        return 0
        #return int(255*self._bright(self.png.pixel(x, y)))
        w, h = self.png.width(), self.png.height()
        dx, dy = 0, 0
        while x+dx < w and self._bright(self.png.getpixel((x + dx, y))) > 0.8 and \
              y+dy < h and self._bright(self.png.getpixel((x, y + dy))) > 0.8 and dx < 55:
            dx += 1 ; dy += 1
            
        return dx

    def _bright(self, qc):
        r, g, b = qc #QColor(qc).getRgbF()
        return math.sqrt((r*r + g*g + b*b) / 3.)



class CrosswordGrid(object):

    def __init__(self, cw):
        self.cw = cw

    def renumber(self):
        cw = self.cw
        in_range = lambda row, col: 0 <= row < len(cw) and 0 <= col < len(cw[row])
        is_vacant = lambda row, col: in_range(row, col) and cw[row][col] == " "
            
        numbered = []
            
        for i, row in enumerate(cw):
            for j, cell in reversed(list(enumerate(row))):  # @UnusedVariable
                if not is_vacant(i, j+1) and is_vacant(i, j) and is_vacant(i, j-1):
                    numbered.append((i, j))
                elif not is_vacant(i-1, j) and is_vacant(i, j) and is_vacant(i+1, j):
                    numbered.append((i, j))

        for idx, (i, j) in enumerate(numbered): cw[i][j] = str(idx+1)

    def output_json(self, out=sys.stdout):
        cw = self.cw
        for r in cw:
            print("#", " ".join("%2s" % x for x in r), file=out)

        print("{", file=out)

        fmt = lambda cell: '"x"' if cell == 'X' else cell

        for i, row in enumerate(cw):
            if i > 0: print(",", file=out)
            print("        %d: {" % (i+1), end=' ', file=out)
            print(", ".join("%d: %s" % (j+1, fmt(cell)) for j, cell in enumerate(row)
                            if cell != " "), "}", end=' ', file=out)
        print("}", file=out)


class Style(object):
    Stroke = namedtuple('Stroke', 'style color')
    Fill = namedtuple('Fill', 'style color')
    Fill.__new__.__defaults__ = (None,)
    def __init__(self):
        self.stroke = self.Stroke('solid', 0)
        self.fill = self.Fill('transparent')
    def with_(self, **kw):
        for k,v in kw.iteritems():
            setattr(self, k, v)
        return self
    DEFAULT=None
Style.DEFAULT = Style()


def detect_grid_and_output_json(png_filename, json_filename=None):
    wb = CrosswordBitmap(MagicNumbers.SIZE, MagicNumbers.SIZE, MagicNumbers.MARGIN_TOP, png_filename)

    cw = wb.detect_grid()
    cw.renumber()

    out = open(json_filename, 'w') if json_filename else sys.stdout
    cw.output_json(out)
    


if __name__ == '__main__':
    import sys
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("png-filename")
    a.add_argument('--size', type=int, nargs='?', default=MagicNumbers.SIZE)
    a.add_argument('--margin-top', type=int, nargs='?', default=MagicNumbers.MARGIN_TOP)
    a.add_argument('--cropped', action='store_true')
    a = a.parse_args()
    if a.cropped:
        a.size = None
        a.margin_top = 0
    wb = CrosswordBitmap(a.size, a.size, a.margin_top, png_filename=getattr(a, 'png-filename'))

    if 0:
        a = QApplication(sys.argv)
        w = QMainWindow()
        fb = FrameBuffer(QSize(800, 800), w)
        wb.raster(fb.fb)
        w.setCentralWidget(fb)
        w.resize(QSize(700, 700))
        w.show(); w.raise_()
        a.exec_()
    
    else:
        cw = wb.detect_grid()
        cw.renumber()
        
        cw.output_json()
