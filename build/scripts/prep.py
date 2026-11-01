"""Convert the Claude Docs markdown export of the EOP translation into
pandoc markdown with raw LaTeX hooks for the typeset PDF."""
import re
import sys

SRC, DST = sys.argv[1], sys.argv[2]
text = open(SRC, encoding="utf-8").read()

SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUPMAP = str.maketrans(SUP, "0123456789")
SUPRE = f"[{SUP}]+"

FIGS = {
    "5-i": "img/fig5-i.png",
    "5-ii": "img/fig5-ii.jpg",
    "7-i": "img/fig7-i.jpg",
    "7-ii": "img/fig7-ii.jpg",
}


def tex_escape(s):
    rep = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(rep.get(c, c) for c in s)


def raw(block):
    return "\n```{=latex}\n" + block + "\n```\n"


def unescape_md(s):
    s = s.replace("&#91;", "[")
    return re.sub(r"\\([\[\]<>*_])", r"\1", s)


lines = text.split("\n")

# 1. drop everything before the abbreviations (cover + rights are typeset by hand)
start = next(i for i, l in enumerate(lines) if l.startswith("## Abbreviazioni"))
lines = lines[start:]

# 2. collect footnote definitions and drop them (and the --- separators)
notes = {}
body = []
for l in lines:
    m = re.match(rf"^({SUPRE})\s+(.*)$", l)
    if m:
        notes[int(m.group(1).translate(SUPMAP))] = m.group(2)
        continue
    if l.strip() == "---":
        continue
    body.append(l)
assert len(notes) == 99, len(notes)

out = []
i = 0
chapter_lead_pending = False
front_lead_pending = False
in_abbr = False
abbr_rows = []
in_dialog = False


def flush_dialog():
    global in_dialog
    if in_dialog:
        out.append(":::\n")
        in_dialog = False


while i < len(body):
    l = body[i]

    # --- abbreviations table -> two-column list
    if l.startswith("## Abbreviazioni"):
        out.append(raw(r"\eopfront{Abbreviazioni}{abbreviazioni}"))
        in_abbr = True
        i += 1
        continue
    if in_abbr:
        if l.startswith("| ") and not l.startswith("| Sigla") and not l.startswith("| ---"):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            abbr_rows.append(cells)
        elif l.startswith("## "):
            items = "\n".join(
                rf"\eopabbr{{{tex_escape(a)}}}{{{tex_escape(b)}}}" for a, b in abbr_rows
            )
            out.append(raw(r"\begin{eopabbrlist}" + "\n" + items + "\n" + r"\end{eopabbrlist}"))
            in_abbr = False
            continue
        elif l.strip() and not l.startswith("|"):
            out.append(raw(r"{\small " + tex_escape(l.strip()) + r"\par}"))  # intro sentence
        i += 1
        continue

    # --- headings
    m = re.match(r"^## PARTE ([AB]): (.*)$", l)
    if m:
        flush_dialog()
        ptitle = m.group(2).capitalize()
        out.append(raw(rf"\eoppart{{{m.group(1)}}}{{{tex_escape(ptitle)}}}"))
        i += 1
        continue
    m = re.match(r"^## (\d+) (.*)$", l)
    if m:
        flush_dialog()
        out.append(raw(rf"\eopchapter{{{m.group(1)}}}{{{tex_escape(m.group(2))}}}"))
        chapter_lead_pending = True
        i += 1
        continue
    m = re.match(r"^## (.*)$", l)
    if m:
        flush_dialog()
        title = m.group(1)
        label = re.sub(r"[^a-z]", "", title.lower())
        cmd = "eopfrontcont" if label in ("ringraziamenti", "noteallettore", "notalegale") else "eopfront"
        out.append(raw(rf"\{cmd}{{{tex_escape(title)}}}{{{label}}}"))
        front_lead_pending = True
        i += 1
        continue
    m = re.match(r"^(#{3,5}) ([\d.]+) (.*)$", l)
    if m:
        flush_dialog()
        level = {3: "eopsection", 4: "eopsubsection", 5: "eopsubsubsection"}[len(m.group(1))]
        out.append(raw(rf"\{level}{{{m.group(2)}}}{{{tex_escape(m.group(3))}}}"))
        i += 1
        continue

    # --- figures: placeholder + italic caption
    m = re.match(r"^&#91;image: Figura ([\d]+-[iv]+):", l)
    if m:
        key = m.group(1)
        j = i + 1
        while not body[j].strip():
            j += 1
        cap = body[j].strip().strip("*")
        cap = unescape_md(cap)
        cap = re.sub(r"^Figura [\d]+-[iv]+:\s*", "", cap)
        out.append(raw(rf"\eopfigure{{{FIGS[key]}}}{{{key}}}{{{tex_escape(cap)}}}"))
        i = j + 1
        continue

    # --- table captions
    m = re.match(r"^\*\*Tabella ([\d]+-[A-C]): (.*)\*\*$", l)
    if m:
        out.append(raw(rf"\eoptablecaption{{{m.group(1)}}}{{{tex_escape(unescape_md(m.group(2)))}}}"))
        i += 1
        continue

    # --- warning paragraphs
    if l.startswith("**!** "):
        flush_dialog()
        out.append("::: warn\n" + l[6:] + "\n:::")
        i += 1
        continue

    # --- QSO dialogue paragraphs (• / ◦ at line start, outside lists/quotes)
    if re.match(r"^[•◦] ", l):
        if not in_dialog:
            out.append("::: dialog")
            in_dialog = True
        out.append(l)
        i += 1
        continue
    if in_dialog and l.strip() and not re.match(r"^[•◦] ", l):
        flush_dialog()

    # --- small-caps lead-in for chapter openings
    if chapter_lead_pending and l.strip():
        m = re.match(r"^((?:[A-ZÀÈÉÌÒÙ'’0-9.]+\s?)+?)(?=\s[a-zàèéìòù]|,)", l)
        if m:
            lead = m.group(1).strip()
            l = rf"`\eoplead{{{tex_escape(lead.lower())}}}`{{=latex}}" + l[len(m.group(1)):]
        chapter_lead_pending = False
    elif front_lead_pending and l.strip():
        words = l.split(" ")
        lead = " ".join(words[:3])
        l = rf"`\eoplead{{{tex_escape(lead.lower())}}}`{{=latex}} " + " ".join(words[3:])
        front_lead_pending = False

    out.append(l)
    i += 1

flush_dialog()
md = "\n".join(out)

def wrap_pair(md, a, b, wa, wb):
    ia = md.index("\\eoptablecaption{%s}" % a)
    ia = md.rfind("```{=latex}", 0, ia)
    ib = md.index("\\eoptablecaption{%s}" % b)
    # end of table B = first blank line after its last table row
    tb = md.index("\n|", ib)
    end = tb
    for line in md[tb+1:].split("\n"):
        if not line.startswith("|"):
            break
        end += len(line) + 1
    return md[:ia] + "\n::: {.sbs wa=%s wb=%s}\n\n" % (wa, wb) + md[ia:end+1] + "\n:::\n" + md[end+1:]

md = wrap_pair(md, "11-A", "11-B", "0.52", "0.45")
md = wrap_pair(md, "13-A", "13-B", "0.44", "0.52")


def move_fig_before(md, key, anchor):
    """Move a figure block up so it wraps the text that refers to it."""
    s = md.index("\\eopfigure{%s}{%s}" % (FIGS[key], key))
    s = md.rfind("```{=latex}", 0, s)
    e = md.index("```", md.index("\n", s + 12)) + 3
    block = md[s:e]
    md = md[:s] + md[e:]
    a = md.index(anchor)
    return md[:a] + block + "\n\n" + md[a:]

# dove ancorare le figure, per versione (schermo o stampa 17x24):
# ogni figura sta accanto al testo che la cita e riempie la pagina senza lasciare vuoti
import json, os
LAYOUT = sys.argv[3] if len(sys.argv) > 3 else "screen"
ANCHORS = {
    "screen": {"5-i": "Se sembra che la causa sia la tua stazione",
               "5-ii": "È fondamentale anche rivedere"},
    "print": {"5-i": "Se sembra che la causa sia la tua stazione",
              "5-ii": "I tempi di salita e di discesa"},
}
if os.environ.get("EOP_ANCHORS"):  # per le prove: {"5-i": "..."}
    ANCHORS[LAYOUT] = json.loads(os.environ["EOP_ANCHORS"])
for key, anchor in ANCHORS[LAYOUT].items():
    md = move_fig_before(md, key, anchor)


def move_pair_before(md, key, anchor):
    """Sposta un blocco di tabelle affiancate (non spezzabile) prima di `anchor`."""
    c = md.index("\\eoptablecaption{%s}" % key)
    s = md.rfind("\n::: {.sbs", 0, c)
    e = md.index("\n:::\n", c) + len("\n:::\n")
    block = md[s:e]
    md = md[:s] + "\n" + md[e:]
    a = md.index(anchor)
    return md[:a] + block.lstrip("\n") + "\n" + md[a:]


# tabelle affiancate: subito dopo il paragrafo che le annuncia, se serve a evitare vuoti
PAIR_ANCHORS = {"screen": {}, "print": {"11-A": "Quando parli, accentua la sillaba"}}
for key, anchor in PAIR_ANCHORS[LAYOUT].items():
    md = move_pair_before(md, key, anchor)

# bold uppercase run-in labels (AMICIZIA., R – LEGGIBILITÀ (READABILITY).) -> small caps
md = re.sub(r"\*\*([A-ZÀÈÉÌÒÙ][A-ZÀÈÉÌÒÙ ,'’()–-]+\.)\*\*",
            lambda m: rf"`\eoplabel{{{tex_escape(m.group(1).lower())}}}`{{=latex}}", md)

# overline prosign notation (A̅R̅)
md = md.replace("A̅R̅", r"`\eopbar{AR}`{=latex}")

# footnote references -> pandoc footnotes; keep "83 84" style pairs readable
def fnref(m):
    n = int(m.group(0).translate(SUPMAP))
    return f"[^{n}]"

md = re.sub(rf"({SUPRE})\s({SUPRE})", lambda m: fnref(re.match(SUPRE, m.group(1))) + r"`\eopfnsep{}`{=latex}" + fnref(re.match(SUPRE, m.group(2))), md)
md = re.sub(SUPRE, fnref, md)

md += "\n\n" + "\n\n".join(f"[^{n}]: {notes[n]}" for n in sorted(notes)) + "\n"
open(DST, "w", encoding="utf-8").write(md)
print("ok", len(md))
