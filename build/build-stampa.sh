#!/bin/sh
# Genera i file per la stampa in brossura 16,5x24 cm (formato 4graph): interno e
# copertina (quarta + dorso + prima), entrambi con 3 mm di abbondanza per lato.
# Uso: ./build/build-stampa.sh [spessore del dorso in mm, default 5.84 = 92 pagine, patinata 135 g]
# Lo spessore giusto lo indica la tipografia in base a carta e numero di pagine.
# Il formato si cambia in scripts/make_print.py (TRIM_W, TRIM_H) e qui sotto (TRIMW).
set -e
cd "$(dirname "$0")"
SPINE=${1:-5.84}
TRIMW=165
OUT=../dist/stampa-165x240
python3 scripts/prep.py ../src/eop-it.md prepped-stampa.md print
pandoc prepped-stampa.md -f markdown+raw_tex+raw_attribute+fenced_divs -t latex \
  --lua-filter scripts/eop.lua -o body-stampa.tex
python3 scripts/make_print.py
for i in 1 2 3; do xelatex -interaction=nonstopmode -halt-on-error main-stampa.tex > /dev/null; done
for i in 1 2; do
  xelatex -interaction=nonstopmode -halt-on-error -jobname=copertina-stampa-out \
    "\def\eoptrimw{$TRIMW}\def\eopspine{$SPINE}\input{copertina-stampa}" > /dev/null
done
mkdir -p "$OUT"
# CMYK FOGRA51 (PSO Coated v3) + PDF/X-3, poi TrimBox/BleedBox
python3 scripts/to_cmyk.py main-stampa.pdf main-stampa-cmyk.pdf "Etica e procedure operative - interno"
python3 scripts/to_cmyk.py copertina-stampa-out.pdf copertina-stampa-cmyk.pdf "Etica e procedure operative - copertina"
python3 scripts/set_boxes.py main-stampa-cmyk.pdf "$OUT/IARU-EOP-165x240-interno.pdf"
python3 scripts/set_boxes.py copertina-stampa-cmyk.pdf "$OUT/IARU-EOP-165x240-copertina-dorso-${SPINE}mm.pdf"
echo "File di stampa generati in dist/stampa-165x240/"
