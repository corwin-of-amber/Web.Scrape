import PIL
import cv2  # not used directly; but make sure you have it.
            # pyscreeze is slow and sometimes fails to detect when it is not installed.
import pyscreeze
import os.path
import re
from web_resource.document import WebDocument, FileDocument



ROOT = os.path.join(os.path.dirname(__file__), "res")


def open_uri(uri):
    if uri.startswith("http://") or uri.startswith("https://"):
        mo = re.match('(.*)_gen/derivative', uri)
        if mo: uri = mo.group(1)
        uri = re.sub('/w_.*?/', '/', uri)
        document = WebDocument(uri)
    else:
        document = FileDocument(uri, encoding=FileDocument.ENCODING_BINARY)

    return document


def crop(im):
    corners = ["top-left", "top-right", "bottom-left", "bottom-right"]

    sightings = [pyscreeze.locate(os.path.join(ROOT, "%s.png" % c), im) for c in corners]

    print(sightings)

    if all(s is None for s in sightings):
        return None
    else:
        x0 = min(s[0] for s in sightings if s is not None)
        y0 = min(s[1] for s in sightings if s is not None)
        x1 = max(s[0] + s[2] for s in sightings if s is not None)
        y1 = max(s[1] + s[3] for s in sightings if s is not None)

        return im.crop((x0, y0, x1, y1))


if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("image_filename")
    a = a.parse_args()

    document = open_uri(a.image_filename)
    document.save_as_file("cross.png")

    im = PIL.Image.open(document.access_as_file())

    body = crop(im)

    if not body:
        print("Not found.")
    else:
        body.save("body.png")
        print("Wrote body.png.")
