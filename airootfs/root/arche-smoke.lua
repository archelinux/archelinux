assert(vim.v.errmsg == "", vim.v.errmsg)
for _, name in ipairs({ "lua_ls", "rust_analyzer", "basedpyright", "gopls" }) do
  assert(vim.lsp.is_enabled(name), name .. " not enabled")
  assert(vim.fn.executable(vim.lsp.config[name].cmd[1]) == 1, name .. " missing executable")
end
for lang, sample in pairs({ lua = "local x = 1", python = "x = 1", rust = "fn main() {}" }) do
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, { sample })
  vim.treesitter.language.add(lang)
  assert(vim.treesitter.query.get(lang, "highlights"), lang .. " missing queries")
  assert(vim.treesitter.get_parser(buf, lang):parse()[1], lang .. " failed to parse")
  vim.treesitter.start(buf, lang)
end
print("Neovim LSP and parser smoke checks passed")

-- Opening an unseeded language must not raise a FileType/BufRead error.
local svg = vim.fn.tempname() .. ".svg"
vim.fn.writefile({ '<svg xmlns="http://www.w3.org/2000/svg"/>' }, svg)
vim.cmd("edit " .. vim.fn.fnameescape(svg))
assert(vim.v.errmsg == "", vim.v.errmsg)
vim.cmd("vsplit " .. vim.fn.fnameescape(svg))
assert(vim.v.errmsg == "", vim.v.errmsg)
vim.fn.delete(svg)
print("Unseeded SVG filetype and split regression passed")
