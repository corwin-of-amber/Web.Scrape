cp ${1:-birman.png} ~/var/workspace/Web.Crossword/data/birman.png
if [ -z $2 ] ; then python3 cut.py ${1:-birman.png} ; fi
python3 squares.py --cropped ${2:-body.png} > ~/var/workspace/Web.Crossword/data/grid.json
