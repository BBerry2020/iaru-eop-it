-- Pandoc Lua filter for the Italian EOP typesetting.

local function latex(blocks)
  return pandoc.write(pandoc.Pandoc(blocks), 'latex')
end

local function wrap(env, blocks, opt)
  local out = { pandoc.RawBlock('latex', '\\begin{' .. env .. '}' .. (opt or '')) }
  for _, b in ipairs(blocks) do table.insert(out, b) end
  table.insert(out, pandoc.RawBlock('latex', '\\end{' .. env .. '}'))
  return out
end

function Div(el)
  if el.classes:includes('sbs') then
    local wa = el.attributes['wa'] or '0.48'
    local wb = el.attributes['wb'] or '0.48'
    local parts, cur = {}, {}
    for _, b in ipairs(el.content) do
      if b.t == 'RawBlock' then
        local txt = b.text
        if txt:find('\\eoptablecaption') then
          if #cur > 0 then table.insert(parts, cur) end
          cur = {txt}
        else
          txt = txt:gsub('\\begin{eoptable}', '\\begin{eopsmalltable}')
                   :gsub('\\end{eoptable}', '\\end{eopsmalltable}')
                   :gsub('%%%%EOPCAP:%d+:%%%%\n', '')
                   :gsub('\\endfirsthead\n.-\\endhead\n', '')
                   :gsub('\\nopagebreak\n', '')
          table.insert(cur, txt)
        end
      end
    end
    if #cur > 0 then table.insert(parts, cur) end
    local out = '\\par\\needspace{12\\baselineskip}\\noindent\\begin{minipage}[t]{' .. wa .. '\\linewidth}\n'
      .. table.concat(parts[1], '\n') .. '\n\\end{minipage}\\hfill\\begin{minipage}[t]{' .. wb .. '\\linewidth}\n'
      .. table.concat(parts[2], '\n') .. '\n\\end{minipage}\\par\\vspace{8pt}'
    return pandoc.RawBlock('latex', out)
  end
  if el.classes:includes('warn') then
    return wrap('eopwarn', el.content)
  elseif el.classes:includes('dialog') then
    local c = el.content
    local inner = {}
    for i, b in ipairs(c) do
      if i == 2 or (i == #c and #c > 2) then
        table.insert(inner, pandoc.RawBlock('latex', '\\nopagebreak'))
      end
      table.insert(inner, b)
    end
    local out = { pandoc.RawBlock('latex', '\\par\\nopagebreak') }
    for _, b in ipairs(wrap('eopdialog', inner)) do table.insert(out, b) end
    return out
  end
end

function BlockQuote(el)
  return wrap('eopnote', el.content)
end

function CodeBlock(el)
  if el.classes:includes('latex') then
    -- formula semplice resa nel carattere del testo (niente font matematici Computer Modern)
    local s = el.text:gsub('\\text{([^}]*)}', '%1'):gsub('\\times', '×'):gsub('%s*=%s*', ' = ')
    return pandoc.RawBlock('latex', '\\par\\nopagebreak\\begin{center}' .. s .. '\\end{center}')
  end
  return pandoc.RawBlock('latex',
    '\\par\\nopagebreak\\begin{eopqso}\n\\begin{Verbatim}\n' .. el.text .. '\n\\end{Verbatim}\n\\end{eopqso}')
end

-- Tables: own longtable with sans header, zebra rows and computed widths.
local function cell_text(cell)
  return pandoc.utils.stringify(cell.contents)
end

local function cell_latex(cell)
  local s = latex(cell.contents)
  s = s:gsub('%s+$', '')
  return s
end

function Table(tbl)
  local head_rows = tbl.head.rows
  local body_rows = {}
  for _, b in ipairs(tbl.bodies) do
    for _, r in ipairs(b.body) do table.insert(body_rows, r) end
  end
  local ncols = #tbl.colspecs

  -- widths from content length (sqrt damping), with minimum share
  local len = {}
  for c = 1, ncols do len[c] = 1 end
  local allrows = {}
  for _, r in ipairs(head_rows) do table.insert(allrows, r) end
  for _, r in ipairs(body_rows) do table.insert(allrows, r) end
  for _, r in ipairs(allrows) do
    for c, cell in ipairs(r.cells) do
      local n = utf8.len(cell_text(cell)) or #cell_text(cell)
      if n > len[c] then len[c] = n end
    end
  end
  local total = 0
  local w = {}
  for c = 1, ncols do w[c] = math.sqrt(math.min(len[c], 90)); total = total + w[c] end
  for c = 1, ncols do
    w[c] = w[c] / total
    if w[c] < 0.12 then w[c] = 0.12 end
  end
  total = 0
  for c = 1, ncols do total = total + w[c] end

  -- detect the 80 m band plan table: fixed, readable widths
  if #head_rows > 0 and ncols == 5 and cell_text(head_rows[1].cells[3]):find('Larghezza di banda') then
    local fixed = {0.09, 0.17, 0.13, 0.19, 0.42}
    for c = 1, ncols do w[c] = fixed[c] end
    total = 1
  end

  local spec = '@{}'
  for c = 1, ncols do
    spec = spec .. string.format('>{\\raggedright\\arraybackslash}p{\\dimexpr %.4f\\linewidth-2\\tabcolsep\\relax}', w[c] / total)
  end
  spec = spec .. '@{}'

  -- detect the 80 m band plan table (colour rows by bandwidth)
  local is_bandplan = false
  if #head_rows > 0 and ncols >= 3 then
    local h3 = cell_text(head_rows[1].cells[3])
    if h3:find('Larghezza di banda') then is_bandplan = true end
  end

  local lines = {}
  table.insert(lines, '\\begin{eoptable}{' .. spec .. '}')
  local function row_tex(r, header)
    local cells = {}
    local notes = {}
    for c, cell in ipairs(r.cells) do
      -- le note a piè di pagina escono dalla cella: \footnotemark nella cella e
      -- \footnotetext subito dopo la riga, così la tabella può spezzarsi tra due pagine
      local contents = cell.contents:walk({
        Note = function(n)
          table.insert(notes, (latex(n.content):gsub('%s+$', '')))
          return pandoc.RawInline('latex', '\\footnotemark{}')
        end
      })
      local s = (latex(contents):gsub('%s+$', ''))
      if header then
        -- intestazione centrata in verticale nella sua cella
        local pre = (c == 1) and '@{}' or ''
        local post = (c == ncols) and '@{}' or ''
        s = string.format('\\multicolumn{1}{%s>{\\raggedright\\arraybackslash}m{\\dimexpr %.4f\\linewidth-2\\tabcolsep\\relax}%s}{\\eopth{%s}}',
          pre, w[c] / total, post, s)
      end
      table.insert(cells, s)
    end
    local row = table.concat(cells, ' & ') .. ' \\\\'
    if #notes > 0 then
      local nt = '\\noalign{\\addtocounter{footnote}{-' .. #notes .. '}'
      for _, n in ipairs(notes) do
        nt = nt .. '\\stepcounter{footnote}\\footnotetext{' .. n .. '}'
      end
      row = row .. '\n' .. nt .. '}'
    end
    return row
  end
  -- prima intestazione (con la didascalia) e intestazione ripetuta sulle pagine successive
  table.insert(lines, '%%EOPCAP:' .. ncols .. ':%%')
  for _, r in ipairs(head_rows) do
    table.insert(lines, '\\rowcolor{eophead}' .. row_tex(r, true))
  end
  table.insert(lines, '\\endfirsthead')
  table.insert(lines, '%%EOPCAPCONT:' .. ncols .. ':%%')
  for _, r in ipairs(head_rows) do
    table.insert(lines, '\\rowcolor{eophead}' .. row_tex(r, true))
  end
  table.insert(lines, '\\endhead')
  for idx, r in ipairs(body_rows) do
    local prefix = ''
    if is_bandplan then
      local bw = cell_text(r.cells[3])
      if bw == '200' then prefix = '\\rowcolor{bp200}'
      elseif bw == '500' then prefix = '\\rowcolor{bp500}'
      else prefix = '\\rowcolor{bp2700}' end
    elseif idx % 2 == 0 then
      prefix = '\\rowcolor{eopzebra}'
    end
    table.insert(lines, prefix .. row_tex(r, false))
    -- didascalia e intestazione mai da sole in fondo alla pagina: almeno due righe con loro
    if idx <= 1 and #body_rows > 2 then table.insert(lines, '\\nopagebreak') end
  end
  table.insert(lines, '\\end{eoptable}')
  return pandoc.RawBlock('latex', table.concat(lines, '\n'))
end

-- La didascalia "Tabella X: ..." entra nella tabella: resta sempre attaccata
-- all'intestazione e si ripete, con "(continua)", quando la tabella va a pagina nuova.
local function caprow(n, num, txt)
  return string.format('\\multicolumn{%d}{@{}>{\\raggedright\\arraybackslash}p{\\dimexpr\\linewidth-2\\tabcolsep\\relax}@{}}{\\eopcaprow{%s}{%s}}\\\\[3pt]', n, num, txt)
end

function Blocks(blocks)
  local out = pandoc.List()
  local i = 1
  while i <= #blocks do
    local b, nxt = blocks[i], blocks[i + 1]
    local num, txt
    if b.t == 'RawBlock' then
      num, txt = b.text:match('^%s*\\eoptablecaption{([^}]*)}{(.*)}%s*$')
    end
    if num and nxt and nxt.t == 'RawBlock' and nxt.text:find('%%%%EOPCAP:') then
      local s = nxt.text
      s = s:gsub('%%%%EOPCAP:(%d+):%%%%', function(n) return caprow(tonumber(n), num, txt) end)
      s = s:gsub('%%%%EOPCAPCONT:(%d+):%%%%', function(n)
        return caprow(tonumber(n), num, txt .. ' \\textit{(continua)}') end)
      out:insert(pandoc.RawBlock('latex', s))
      i = i + 2
    else
      if b.t == 'RawBlock' and b.text:find('%%%%EOPCAP') then
        b = pandoc.RawBlock('latex', (b.text:gsub('%%%%EOPCAP[A-Z]*:%d+:%%%%\n', '')))
      end
      out:insert(b)
      i = i + 1
    end
  end
  return out
end

-- URL-like links: let the visible path break anywhere (xurl)
local function esc(s)
  return (s:gsub('\\', '/'):gsub('%%', '\\%%'):gsub('#', '\\#'))
end

function Link(el)
  local txt = pandoc.utils.stringify(el.content)
  if not txt:find('%s') and (txt:find('/') or txt:find('%.')) then
    return pandoc.RawInline('latex', '\\href{' .. esc(el.target) .. '}{\\nolinkurl{' .. esc(txt) .. '}}')
  end
end
