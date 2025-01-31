local wezterm = require("wezterm")

local config = wezterm.config_builder()

config.default_prog = { '/usr/bin/env', 'zsh', '-l' }

local appearance = wezterm.gui.get_appearance()
if appearance == "Dark" then
  config.color_scheme = "Hemisu Dark (Gogh)"
else
  config.color_scheme = "Hemisu Light (Gogh)"
end

config.hide_tab_bar_if_only_one_tab = true
config.window_close_confirmation = "NeverPrompt"

config.keys = {
  {
    key = "LeftArrow",
    mods = "OPT",
    action = wezterm.action({
      SendString = "\x1bb",
    }),
  },
  {
    key = "RightArrow",
    mods = "OPT",
    action = wezterm.action({
      SendString = "\x1bf",
    }),
  },
}

return config
