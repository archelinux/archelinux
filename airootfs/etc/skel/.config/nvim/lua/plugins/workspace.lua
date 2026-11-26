local has_system_lua_ls = vim.fn.executable("lua-language-server") == 1

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
      ensure_installed = has_system_lua_ls and {} or { "lua_ls" },
    },
  },
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        lua_ls = { mason = not has_system_lua_ls },
      },
    },
  },
}
