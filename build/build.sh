#!/bin/sh
# Genera il PDF impaginato da src/eop-it.md (richiede pandoc >= 3, XeLaTeX,
# TeX Live con polyglossia e i pattern di sillabazione italiani).
set -e
cd "$(dirname "$0")"
python3 scripts/prep.py ../src/eop-it.md prepped.md
pandoc prepped.md -f markdown+raw_tex+raw_attribute+fenced_divs -t latex \
  --lua-filter scripts/eop.lua -o body.tex
for i in 1 2 3; do xelatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null; done
cp main.pdf ../dist/IARU-EOP-4a-edizione-traduzione-italiana-non-ufficiale.pdf
echo "PDF generato in dist/"
