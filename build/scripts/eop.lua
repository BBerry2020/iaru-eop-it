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
  if el.classes:includes('warn') then
    return wrap('eopwarn', el.content)
  elseif el.classes:includes('dialog') then
    return wrap('eopdialog', el.content)
  end
end

function BlockQuote(el)
  return wrap('eopnote', el.content)
end

function CodeBlock(el)
  if el.classes:includes('latex') then
    return pandoc.RawBlock('latex', '\\[ ' .. el.text .. ' \\]')
  end
  return pandoc.RawBlock('latex',
    '\\begin{eopqso}\n\\begin{Verbatim}\n' .. el.text .. '\n\\end{Verbatim}\n\\end{eopqso}')
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
    if w[c] < 0.09 then w[c] = 0.09 end
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
    for _, cell in ipairs(r.cells) do
      local s = cell_latex(cell)
      if header then s = '\\eopth{' .. s .. '}' end
      table.insert(cells, s)
    end
    return table.concat(cells, ' & ') .. ' \\\\'
  end
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
  end
  table.insert(lines, '\\end{eoptable}')
  return pandoc.RawBlock('latex', table.concat(lines, '\n'))
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
