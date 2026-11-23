for key, direction in pairs({ h = "L", j = "D", k = "U", l = "R" }) do
  vim.keymap.set("n", "<C-" .. key .. ">", function()
    local previous = vim.api.nvim_get_current_win()
    vim.cmd.wincmd(key)
    if previous == vim.api.nvim_get_current_win() and vim.env.TMUX then
      vim.system({ "tmux", "select-pane", "-" .. direction })
    end
  end)
end
