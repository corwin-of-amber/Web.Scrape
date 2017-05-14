cp ${1:=birman.png} ~/var/workspace/Web.RealTime/apps/crossword/data/birman.png
python squares.py --cropped ${2:=body.png} > ~/var/workspace/Web.RealTime/apps/crossword/data/grid.json
