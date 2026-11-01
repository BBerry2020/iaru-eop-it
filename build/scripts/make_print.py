"""Deriva main-stampa.tex (interno per la stampa in brossura) da main.tex
(versione a schermo). Uso: python3 scripts/make_print.py
Il formato rifilato si cambia qui sotto (TRIM_W x TRIM_H, in mm)."""
import re

SRC, DST = "main.tex", "main-stampa.tex"
TRIM_W, TRIM_H = 165, 240        # formato 4graph 16,5x24 cm
INNER, OUTER = 19, 14            # margine verso il dorso / verso il taglio
BLEED = 3
t = open(SRC, encoding="utf-8").read()


def sub(old, new, count=1):
    global t
    assert old in t, "non trovato: " + old[:60]
    t = t.replace(old, new, count)


def cut(start, end, new):
    """Sostituisce il blocco che va da `start` (incluso) a `end` (escluso)."""
    global t
    a = t.index(start)
    b = t.index(end, a)
    t = t[:a] + new + t[b:]


# fronte/retro: margini speculari, numeri di pagina all'esterno
sub(r"\documentclass[10pt,oneside,openany]{book}",
    r"\documentclass[10pt,twoside,openany]{book}")

# formato rifilato + 3 mm di abbondanza per lato
GEOM = (r"\usepackage[paperwidth=%dmm,paperheight=%dmm," "\n"
        r"  layoutwidth=%dmm,layoutheight=%dmm,layouthoffset=%dmm,layoutvoffset=%dmm," "\n"
        r"  inner=%dmm,outer=%dmm,top=16mm,bottom=18mm," "\n"
        r"  headheight=13pt,headsep=5mm,footskip=9mm,marginparwidth=12mm]{geometry}" "\n"
        r"\newcommand{\eopbleed}{%dmm}") % (
    TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED, TRIM_W, TRIM_H, BLEED, BLEED, INNER, OUTER, BLEED)
t = re.sub(r"\\usepackage\[paperwidth=568\.98bp.*?\]\{geometry\}", lambda m: GEOM, t, count=1, flags=re.S)
assert r"\eopbleed" in t

# testatina e piede: niente link (su carta non servono), tutto speculare
cut(r"\fancyhead[L]{", r"\fancypagestyle{eopempty}", r"""\fancyhead[LE,RO]{\footnotesize\color{eopblue}\textsc{iaru} © 2026 · 4.2.0 \textcolor{eopblue!60}{·} \textsc{traduzione italiana non ufficiale}}
\fancyfoot[LE,RO]{\sffamily\footnotesize\thepage}
\fancyfoot[RE]{\parbox[t]{0.86\textwidth}{\raggedleft\sffamily\footnotesize\FirstMark{eop}}}
\fancyfoot[LO]{\parbox[t]{0.86\textwidth}{\raggedright\sffamily\footnotesize\FirstMark{eop}}}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[LE,RO]{\sffamily\footnotesize\thepage}}
""")

# pagine di parte: la fascia va al vivo (abbondanza inclusa), il testo resta nel rifilo
sub(r"([yshift=-62mm]current page.north east)", r"([yshift=-58mm]current page.north east)")
sub(r"at ([xshift=-14mm,yshift=-14mm]current page.north east)",
    r"at ([xshift=-16mm,yshift=-15mm]current page.north east)")

# figure: in proporzione alla giustezza, quasi la stessa misura fisica della versione a schermo
for k, v in (("5-i", "0.65"), ("5-ii", "0.65"), ("7-i", "0.58"), ("7-ii", "0.58")):
    t = re.sub(r"(\\csname eopfw@%s\\endcsname\{)[\d.]+\}" % re.escape(k),
               lambda m: m.group(1) + v + "}", t, count=1)

# abbreviazioni: su due pagine, quindi corpo più grande e più aria
sub(r"\begin{multicols}{2}\fontsize{7}{7.95}\selectfont",
    r"\begin{multicols}{2}\fontsize{ABBRFS}\selectfont")
sub(r"\setlength{\eopabbrsep}{2.5pt plus 1.5pt}", r"\setlength{\eopabbrsep}{ABBRSEP}")
t = t.replace("ABBRFS", "8.8}{10.5").replace("ABBRSEP", "4.4pt plus 1.5pt")

# colori per la stampa (linee guida 4graph): CMYK con profilo FOGRA51 (PSO Coated v3),
# valori calcolati dagli originali sRGB con intento colorimetrico relativo;
# testo nero al 100% K, senza ciano, magenta e giallo (niente fuori registro)
sub(r"\usepackage[table]{xcolor}", r"\usepackage[table,cmyk]{xcolor}")
CMYK = {
    "eopblue": "0.85,0.45,0.02,0", "eopteal": "0.77,0.11,0.17,0.13",
    "eopcream": "0.02,0.07,0.44,0", "eopink": "0,0,0,1",
    "eophead": "0.15,0.04,0.02,0", "eopzebra": "0.05,0.02,0.02,0",
    "eopnoteback": "0.07,0.02,0.02,0", "eopaccent": "0.05,0.89,0.94,0.18",
    "bp200": "0.12,0.04,0.01,0", "bp500": "0.09,0.01,0.11,0", "bp2700": "0.02,0.04,0.14,0",
}
for name, val in CMYK.items():
    t, n = re.subn(r"\\definecolor\{%s\}\{HTML\}\{[0-9A-F]{6}\}" % name,
                   lambda m: r"\definecolor{%s}{cmyk}{%s}" % (name, val), t)
    assert n == 1, name

# numeri dei titoli nel testo e non nel margine: il margine interno deve restare
# libero per 10 mm dal dorso e quello esterno per 5 mm dal taglio
assert t.count(r"\makebox[0pt][r]{") == 4
t = t.replace(r"\makebox[0pt][r]{", "{")

# filetti di almeno 0,5 pt (sotto questo spessore la tipografia non garantisce la resa)
sub(r"\hrule width 30mm height 0.4pt", r"\hrule width 30mm height 0.5pt")
sub(r"{\color{eopteal}\rule{\linewidth}{0.4pt}}", r"{\color{eopteal}\rule{\linewidth}{0.5pt}}")

# testo preparato apposta per la stampa (figure ancorate in punti diversi)
sub(r"\input{body.tex}", r"\input{body-stampa.tex}")

# niente copertina e quarta: vanno nel file della copertina
cut("% ================= COPERTINA =================",
    "% ================= FRONTESPIZIO",
    "")
cut("% ================= QUARTA DI COPERTINA =================",
    r"\end{document}",
    r"""% ================= PAGINE BIANCHE FINALI =================
% la brossura vuole un numero di pagine multiplo di 4
\clearpage
\makeatletter
\@tempcnta=\ReadonlyShipoutCounter
\@tempcntb=\@tempcnta \divide\@tempcntb by 4 \multiply\@tempcntb by 4
\advance\@tempcnta by -\@tempcntb
\ifnum\@tempcnta>0
  \loop\ifnum\@tempcnta<4 \null\thispagestyle{eopempty}\clearpage\advance\@tempcnta by 1 \repeat
\fi
\makeatother
""")

open(DST, "w", encoding="utf-8").write(t)
print("ok", DST)
