"""Deriva main-17x24.tex (interno per la stampa in brossura 17x24 cm)
da main.tex (versione a schermo). Uso: python3 scripts/make_print.py"""
import re

SRC, DST = "main.tex", "main-17x24.tex"
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

# formato rifilato 170x240 mm + 3 mm di abbondanza per lato (176x246 mm)
t = re.sub(
    r"\\usepackage\[paperwidth=568\.98bp.*?\]\{geometry\}",
    lambda m: r"""\usepackage[paperwidth=176mm,paperheight=246mm,
  layoutwidth=170mm,layoutheight=240mm,layouthoffset=3mm,layoutvoffset=3mm,
  inner=20mm,outer=15mm,top=16mm,bottom=18mm,
  headheight=13pt,headsep=5mm,footskip=9mm,marginparwidth=12mm]{geometry}
\newcommand{\eopbleed}{3mm}""",
    t, count=1, flags=re.S)
assert r"\eopbleed" in t

# testatina e piede: niente link (su carta non servono), tutto speculare
cut(r"\fancyhead[L]{", r"\fancypagestyle{eopempty}", r"""\fancyhead[LE,RO]{\footnotesize\color{eopblue}\textsc{iaru} © 2026 · 4.2.0 \textcolor{eopblue!60}{·} \textsc{traduzione italiana non ufficiale}}
\fancyfoot[LE,RO]{\sffamily\footnotesize\thepage}
\fancyfoot[RE]{\parbox[t]{0.86\textwidth}{\raggedleft\sffamily\footnotesize\eopchapmark\ifdefempty{\eopsecmark}{}{ \textcolor{eopblue!70}{·} \eopsecmark}}}
\fancyfoot[LO]{\parbox[t]{0.86\textwidth}{\raggedright\sffamily\footnotesize\eopchapmark\ifdefempty{\eopsecmark}{}{ \textcolor{eopblue!70}{·} \eopsecmark}}}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[LE,RO]{\sffamily\footnotesize\thepage}}
""")

# pagine di parte: la fascia va al vivo (abbondanza inclusa), il testo resta nel rifilo
sub(r"([yshift=-62mm]current page.north east)", r"([yshift=-58mm]current page.north east)")
sub(r"at ([xshift=-14mm,yshift=-14mm]current page.north east)",
    r"at ([xshift=-16mm,yshift=-15mm]current page.north east)")

# figure: stessa misura fisica della versione a schermo
# (giustezza 156,7 mm -> 135 mm: 56% -> 65%, 50% -> 58%)
for k, v in (("5-i", "0.65"), ("5-ii", "0.65"), ("7-i", "0.58"), ("7-ii", "0.58")):
    t = re.sub(r"(\\csname eopfw@%s\\endcsname\{)[\d.]+\}" % re.escape(k),
               lambda m: m.group(1) + v + "}", t, count=1)

# abbreviazioni: su due pagine, quindi corpo più grande e più aria
sub(r"\begin{multicols}{2}\fontsize{7}{7.95}\selectfont",
    r"\begin{multicols}{2}\fontsize{ABBRFS}\selectfont")
sub(r"\setlength{\eopabbrsep}{2.5pt plus 1.5pt}", r"\setlength{\eopabbrsep}{ABBRSEP}")
t = t.replace("ABBRFS", "8.8}{10.5").replace("ABBRSEP", "5pt plus 1.5pt")

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
