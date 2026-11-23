vim.o.background = "dark"
vim.cmd("highlight clear")
vim.g.colors_name = "archevim"

local text = "#d9dde4"
local muted = "#9ba5b4"
local border = "#546071"
local panel = "#0d1014"
local line = "#171b21"
local selection = "#26313f"
local blue = "#9dbfdf"
local teal = "#9acbc0"
local violet = "#c4b6df"
local amber = "#dfc18d"
local red = "#e2a6a6"

local highlights = {
  Normal = { fg = text, bg = "NONE" },
  NormalFloat = { fg = text, bg = panel },
  SnacksPicker = { fg = text, bg = "#000000" },
  SnacksPickerBorder = { fg = border, bg = "#000000" },
  SnacksPickerTitle = { fg = text, bg = "#000000", bold = true },
  FloatBorder = { fg = border, bg = panel },
  FloatTitle = { fg = violet, bg = panel, bold = true },
  CursorLine = { bg = line },
  CursorLineNr = { fg = amber, bold = true },
  LineNr = { fg = muted },
  WinSeparator = { fg = border },
  Visual = { bg = selection },
  Search = { fg = amber, bg = "#342d20" },
  CurSearch = { fg = "#ffe0aa", bg = "#403420", bold = true },
  IncSearch = { link = "CurSearch" },
  MatchParen = { fg = teal, bg = selection, bold = true },
  StatusLine = { fg = text, bg = panel },
  StatusLineNC = { fg = muted, bg = panel },
  TabLineSel = { fg = text, bg = selection, bold = true },
  PmenuSel = { fg = text, bg = selection, bold = true },
  PmenuSbar = { bg = line },
  PmenuThumb = { bg = border },
  ColorColumn = { bg = line },
  DiffAdd = { bg = "#192823" },
  DiffChange = { bg = "#1b2633" },
  DiffDelete = { fg = red, bg = "#302024" },
  DiffText = { fg = blue, bg = selection, bold = true },

  Comment = { fg = muted, italic = true },
  Constant = { fg = amber },
  String = { fg = teal },
  Identifier = { fg = text },
  Function = { fg = blue },
  Statement = { fg = violet },
  PreProc = { fg = violet },
  Type = { fg = blue },
  Special = { fg = amber },
  Operator = { fg = muted },
  Todo = { fg = amber, bold = true },
  Error = { fg = red, bold = true },
  DiagnosticError = { fg = red },
  DiagnosticWarn = { fg = amber },
  DiagnosticInfo = { fg = blue },
  DiagnosticHint = { fg = teal },
}

local groups = {
  Normal = { "NormalNC", "SignColumn", "FoldColumn" },
  NormalFloat = { "Pmenu", "PmenuKind", "PmenuExtra", "SnacksPickerPreview" },
  SnacksPicker = { "SnacksPickerBox", "SnacksPickerInput", "SnacksPickerList" },
  SnacksPickerTitle = { "SnacksPickerInputTitle" },
  SnacksPickerBorder = { "SnacksPickerInputBorder", "SnacksPickerListBorder" },
  CursorLine = { "CursorColumn", "CursorLineSign", "CursorLineFold", "SnacksPickerPreviewCursorLine" },
  PmenuSel = { "PmenuKindSel", "PmenuExtraSel", "WildMenu", "SnacksPickerListCursorLine", "BlinkCmpMenuSelection" },
  StatusLineNC = { "TabLine", "TabLineFill", "StatusLineTermNC", "Folded" },
  StatusLine = { "StatusLineTerm", "WinBar", "WinBarNC" },
  Error = { "ErrorMsg" },
  DiagnosticWarn = { "WarningMsg" },
}

for name, style in pairs(highlights) do
  vim.api.nvim_set_hl(0, name, style)
end
for target, names in pairs(groups) do
  for _, name in ipairs(names) do
    vim.api.nvim_set_hl(0, name, { link = target })
  end
end
