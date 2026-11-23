vim.opt.number = true
vim.opt.termguicolors = true
vim.opt.clipboard = "unnamedplus"
if not vim.env.WAYLAND_DISPLAY or vim.fn.executable("wl-copy") == 0 then
  vim.g.clipboard = {
    name = "OSC 52",
    copy = { ["+"] = require("vim.ui.clipboard.osc52").copy("+"),
             ["*"] = require("vim.ui.clipboard.osc52").copy("*") },
    paste = { ["+"] = function() return vim.fn.getreg('0', 1, true) end,
              ["*"] = function() return vim.fn.getreg('0', 1, true) end },
  }
end
local servers = {
  lua_ls = { cmd = { "lua-language-server" }, filetypes = { "lua" },
    root_markers = { ".luarc.json", ".git" },
    settings = { Lua = { diagnostics = { globals = { "vim" } } } } },
  rust_analyzer = { cmd = { "rust-analyzer" }, filetypes = { "rust" }, root_markers = { "Cargo.toml", ".git" } },
  basedpyright = { cmd = { "basedpyright-langserver", "--stdio" }, filetypes = { "python" }, root_markers = { "pyproject.toml", ".git" } },
  gopls = { cmd = { "gopls" }, filetypes = { "go", "gomod", "gowork" }, root_markers = { "go.work", "go.mod", ".git" } },
}
for name, config in pairs(servers) do
  vim.lsp.config(name, config)
  if vim.fn.executable(config.cmd[1]) == 1 then vim.lsp.enable(name) end
end
vim.api.nvim_create_autocmd("FileType", {
  callback = function(args)
    local lang = vim.treesitter.language.get_lang(vim.bo[args.buf].filetype)
    if not lang then return end
    local ok, parser = pcall(vim.treesitter.get_parser, args.buf, lang)
    if ok and parser then
      vim.treesitter.start(args.buf, lang)
    end
  end,
})
