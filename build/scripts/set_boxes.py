"""Imposta BleedBox (= foglio intero) e TrimBox (= foglio meno 3 mm per lato)
su ogni pagina, così i controlli della tipografia riconoscono il formato rifilato.
Uso: python3 scripts/set_boxes.py ingresso.pdf uscita.pdf"""
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

BLEED = 3 / 25.4 * 72  # 3 mm in punti PDF

src, dst = sys.argv[1], sys.argv[2]
reader = PdfReader(src)
writer = PdfWriter(clone_from=reader)
for page in writer.pages:
    x0, y0, x1, y1 = [float(v) for v in page.mediabox]
    page.bleedbox = RectangleObject([x0, y0, x1, y1])
    page.trimbox = RectangleObject([x0 + BLEED, y0 + BLEED, x1 - BLEED, y1 - BLEED])
writer.write(dst)
print("ok", dst, len(writer.pages), "pagine")
