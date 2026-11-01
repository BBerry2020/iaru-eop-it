"""Converte un PDF per la stampa in CMYK FOGRA51 (PSO Coated v3), come chiede 4graph
per la carta patinata, e lo marca PDF/X-3 con il profilo come OutputIntent.
I colori del testo e della grafica sono già in CMYK dal LaTeX (testo 100% K) e restano
invariati; Ghostscript converte solo le immagini RGB.
Serve Ghostscript e il profilo PSOcoated_v3.icc (pacchetto Debian/Ubuntu "icc-profiles").
Uso: python3 scripts/to_cmyk.py ingresso.pdf uscita.pdf "Titolo"
"""
import os
import subprocess
import sys
import tempfile

PROFILE = os.environ.get("EOP_ICC", "/usr/share/color/icc/PSOcoated_v3.icc")
src, dst, title = sys.argv[1], sys.argv[2], sys.argv[3]
if not os.path.exists(PROFILE):
    sys.exit("Profilo ICC non trovato: %s (installa il pacchetto icc-profiles "
             "o indica il percorso con EOP_ICC)" % PROFILE)

gslib = subprocess.run(["gs", "--version"], capture_output=True, text=True).stdout.strip()
tmpl = open("/usr/share/ghostscript/%s/lib/PDFX_def.ps" % gslib, encoding="latin-1").read()
for old, new in (
    ("/Title (Title)", "/Title (%s)" % title),
    ("/ICCProfile (ISO Coated sb.icc) def", "/ICCProfile (%s) def" % PROFILE),
    ("/OutputCondition (Commercial and specialty printing)",
     "/OutputCondition (Offset commercial printing, coated paper, FOGRA51)"),
    ("/Info (none)", "/Info (PSO Coated v3)"),
    ("/OutputConditionIdentifier (CGATS TR001)", "/OutputConditionIdentifier (FOGRA51)"),
):
    assert old in tmpl, old
    tmpl = tmpl.replace(old, new)

# PDF/X non ammette annotazioni (i link): su carta non servono, si tolgono
from pypdf import PdfReader, PdfWriter
w = PdfWriter(clone_from=PdfReader(src))
for page in w.pages:
    if "/Annots" in page:
        del page["/Annots"]
noannots = dst + ".noannots.pdf"
w.write(noannots)
src = noannots

with tempfile.NamedTemporaryFile("w", suffix=".ps", delete=False, encoding="latin-1") as f:
    f.write(tmpl)
    pdfx = f.name
try:
    subprocess.run([
        "gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dNOOUTERSAVE",
        "--permit-file-read=" + PROFILE,
        "-sDEVICE=pdfwrite", "-dPDFX", "-dCompatibilityLevel=1.4",
        "-sColorConversionStrategy=CMYK", "-sProcessColorModel=DeviceCMYK",
        "-sOutputICCProfile=" + PROFILE, "-dRenderIntent=1",
        "-dPDFSETTINGS=/prepress", "-dDownsampleColorImages=false",
        "-dDownsampleGrayImages=false", "-dDownsampleMonoImages=false",
        "-dEmbedAllFonts=true", "-dSubsetFonts=true",
        "-sOutputFile=" + dst, pdfx, src,
    ], check=True)
finally:
    os.unlink(pdfx)
    os.unlink(noannots)
print("ok", dst)
