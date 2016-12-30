'''
Created on Mar 17, 2014

@author: corwin
'''
import sys
from PyQt4.QtCore import Qt, QSize
from PyQt4.QtGui import QApplication, QMainWindow, QWidget, QPainter, QImage, QColor
from collections import namedtuple
import math


# Some magic numbers
class MagicNumbers:
    MARGIN_TOP = 49


class FrameBuffer(QWidget):
    
    def __init__(self, qsize, parent=None):
        super(FrameBuffer, self).__init__(parent)
        self.fb = QImage(qsize, QImage.Format_RGB32)
        self.fb.fill(Qt.white)
        
    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.drawImage(0, 0, self.fb)


class CrosswordBitmap(object):
    
    def __init__(self, w, h, png_filename="../../output.png"):
        self.w, self.h = w, h
        self.margin_top = MagicNumbers.MARGIN_TOP
        self.png = QImage(png_filename)
        if self.png.isNull(): raise IOError, "image not found"
    
    def raster(self, fb):
        for x in xrange(self.w):
            for y in range(self.h):
                c =  self._near(x, y) * 4
                fb.setPixel(x, y, QColor(c, c, c).rgb())     
             
    def detect_grid(self):
        nrows, ncols = 13, 13                
        cw = [[0] * ncols for _ in xrange(nrows)]
        for row in xrange(nrows):
            for col in xrange(ncols):
                x, y = self._trasnform_xy((col * 700 + 350) / 13,
                                          (row * 700 + 350) / 13)
                is_white = self._bright(self.png.pixel(x, y)) > 0.8
                cw[row][col] = " " if is_white else "X"
                
        return CrosswordGrid(cw)
                             
    def _trasnform_xy(self, x, y):
        return (self.png.width() - (self.w - x),
                y + self.margin_top)
        
    def _near(self, x, y):
        x, y = self._trasnform_xy(x, y)
        if self._bright(self.png.pixel(x, y)) > 0.8: return 255/4
        return 0
        #return int(255*self._bright(self.png.pixel(x, y)))
        w, h = self.png.width(), self.png.height()
        dx, dy = 0, 0
        while x+dx < w and self._bright(self.png.pixel(x + dx, y)) > 0.8 and \
              y+dy < h and self._bright(self.png.pixel(x, y + dy)) > 0.8 and dx < 55:
            dx += 1 ; dy += 1
            
        return dx

    def _bright(self, qc):
        r, g, b, a = QColor(qc).getRgbF()
        return math.sqrt((r*r + g*g + b*b) / 3.) * a



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
            print >>out, "#", " ".join("%2s" % x for x in r)

        print >>out, "{"

        fmt = lambda cell: '"x"' if cell == 'X' else cell

        for i, row in enumerate(cw):
            if i > 0: print >>out, ","
            print >>out, "        %d: {" % (i+1),
            print >>out, ", ".join("%d: %s" % (j+1, fmt(cell)) for j, cell in enumerate(row)
                                   if cell != " "), "}",
        print >>out, "}"


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
    wb = CrosswordBitmap(700, 700, png_filename)

    cw = wb.detect_grid()
    cw.renumber()

    out = open(json_filename, 'w') if json_filename else sys.stdout
    cw.output_json(out)
    


if __name__ == '__main__':
    import sys
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("png-filename")
    a = a.parse_args()
    wb = CrosswordBitmap(700, 700, getattr(a, 'png-filename'))

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
