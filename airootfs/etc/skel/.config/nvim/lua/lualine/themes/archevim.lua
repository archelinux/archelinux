local function mode(foreground)
  return {
    a = { fg = foreground, bg = "#202631", gui = "bold" },
    b = { fg = "#bac2cf", bg = "#171b21" },
    c = { fg = "#d9dde4", bg = "#0d1014" },
  }
end

return {
  normal = mode("#9dbfdf"),
  insert = mode("#9acbc0"),
  visual = mode("#c4b6df"),
  replace = mode("#e2a6a6"),
  command = mode("#dfc18d"),
  terminal = mode("#9acbc0"),
  inactive = mode("#9ba5b4"),
}
