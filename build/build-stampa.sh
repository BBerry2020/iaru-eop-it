#!/bin/sh
# Genera i file per la stampa in brossura 17x24 cm: interno e copertina
# (quarta + dorso + prima), entrambi con 3 mm di abbondanza per lato.
# Uso: ./build/build-stampa.sh [spessore del dorso in mm, default 5.5]
# Lo spessore giusto lo indica la tipografia in base a carta e numero di pagine.
set -e
cd "$(dirname "$0")"
SPINE=${1:-5.5}
python3 scripts/prep.py ../src/eop-it.md prepped-17x24.md print
pandoc prepped-17x24.md -f markdown+raw_tex+raw_attribute+fenced_divs -t latex \
  --lua-filter scripts/eop.lua -o body-17x24.tex
python3 scripts/make_print.py
for i in 1 2 3; do xelatex -interaction=nonstopmode -halt-on-error main-17x24.tex > /dev/null; done
for i in 1 2; do
  xelatex -interaction=nonstopmode -halt-on-error -jobname=copertina-17x24-out \
    "\def\eopspine{$SPINE}\input{copertina-17x24}" > /dev/null
done
mkdir -p ../dist/stampa-17x24
python3 scripts/set_boxes.py main-17x24.pdf ../dist/stampa-17x24/IARU-EOP-17x24-interno.pdf
python3 scripts/set_boxes.py copertina-17x24-out.pdf \
  "../dist/stampa-17x24/IARU-EOP-17x24-copertina-dorso-${SPINE}mm.pdf"
echo "File di stampa generati in dist/stampa-17x24/"
