cp ${1:-birman.png} ~/var/workspace/Web.RealTime/apps/crossword/data/birman.png
if [ -n $2 ] ; then python3 cut.py ${1:-birman.png} ; fi
python3 squares.py --cropped ${2:-body.png} > ~/var/workspace/Web.RealTime/apps/crossword/data/grid.json
