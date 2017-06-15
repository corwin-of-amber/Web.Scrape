import PIL
import pyscreeze
import os.path
import re
from web_resource.document import WebDocument, FileDocument



ROOT = "./res"


if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("image_filename")
    a = a.parse_args()

    uri = a.image_filename
    if uri.startswith("http://") or uri.startswith("https://"):
        mo = re.match('(.*)_gen/derivative', uri)
        if mo: uri = mo.group(1)
        document = WebDocument(uri)
    else:
        document = FileDocument(uri, encoding=FileDocument.ENCODING_BINARY)

    im = PIL.Image.open(document.access_as_file())

    corners = ["top-left", "top-right", "bottom-left", "bottom-right"]

    sightings = [pyscreeze.locate(os.path.join(ROOT, "%s.png" % c), im) for c in corners]

    print(sightings)

    if all(s is None for s in sightings):
        print("Not found.")
    else:
        x0 = min(s[0] for s in sightings if s is not None)
        y0 = min(s[1] for s in sightings if s is not None)
        x1 = max(s[0] + s[2] for s in sightings if s is not None)
        y1 = max(s[1] + s[3] for s in sightings if s is not None)

        body = im.crop((x0, y0, x1, y1))

        body.save("body.png")
        print("Wrote body.png.")
