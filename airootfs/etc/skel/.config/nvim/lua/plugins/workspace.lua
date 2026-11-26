local has_system_lua_ls = vim.fn.executable("lua-language-server") == 1

local has_system_gopls = vim.fn.executable("gopls") == 1
local mason_servers = {}
if not has_system_lua_ls then
  table.insert(mason_servers, "lua_ls")
end
if not has_system_gopls then
  table.insert(mason_servers, "gopls")
end

return {
  {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      opts.ensure_installed = {}
    end,
  },
  {
    "mason-org/mason-lspconfig.nvim",
    opts = {
      -- LazyVim cannot infer install targets until Mason has fetched its registry.
      ensure_installed = mason_servers,
    },
  },
  {
    "stevearc/conform.nvim",
    opts = { formatters_by_ft = { go = { "gofmt" } } },
  },
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        lua_ls = { mason = not has_system_lua_ls },
        gopls = { mason = not has_system_gopls },
      },
    },
  },
}
