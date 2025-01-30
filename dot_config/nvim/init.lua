if vim.g.vscode then
  return
end

-- Basic settings
vim.opt.number = true         -- Show line numbers
vim.opt.relativenumber = true -- Show relative line numbers
vim.opt.mouse = 'a'          -- Enable mouse support
vim.opt.ignorecase = true    -- Ignore case in search
vim.opt.smartcase = true     -- Override ignorecase when search includes uppercase
vim.opt.hlsearch = true      -- Highlight search results
vim.opt.wrap = true          -- Enable line wrapping
vim.opt.breakindent = true   -- Preserve indentation in wrapped lines
vim.opt.tabstop = 2          -- Number of spaces tabs count for
vim.opt.shiftwidth = 2       -- Size of an indent
vim.opt.expandtab = true     -- Use spaces instead of tabs
vim.opt.termguicolors = true -- Enable 24-bit RGB colors

-- Basic key mappings
vim.g.mapleader = ' '        -- Set leader key to space

-- Package manager setup
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- Plugin specifications
require("lazy").setup({
  -- https://github.com/scottmckendry/cyberdream.nvim
  {
    "scottmckendry/cyberdream.nvim",
    priority = 1000,
    config = function()
      vim.cmd.colorscheme 'cyberdream'
    end
  },

  -- https://github.com/nvim-neo-tree/neo-tree.nvim
  {
    "nvim-neo-tree/neo-tree.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "nvim-tree/nvim-web-devicons",
      "MunifTanjim/nui.nvim",
    },
    keys = {
      { "<leader>e", "<cmd>Neotree toggle<cr>", desc = "Toggle Explorer" },
    },
  },

  -- https://github.com/nvim-telescope/telescope.nvim
  {
    "nvim-telescope/telescope.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    keys = {
      { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find Files" },
      { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Live Grep" },
    },
  },

  -- https://github.com/nvim-treesitter/nvim-treesitter
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    config = function()
      require("nvim-treesitter.configs").setup({
        ensure_installed = "all",
        highlight = { enable = true },
      })
    end,
  },

  -- https://github.com/zbirenbaum/copilot.lua
  {
    "zbirenbaum/copilot.lua",
    cmd = "Copilot",
    event = "InsertEnter",
    config = function()
      require("copilot").setup({
        suggestion = {
          enabled = true,
          auto_trigger = true,
          keymap = {
            accept = "<Tab>",
            next = "<M-]>",
            prev = "<M-[>",
            dismiss = "<C-]>",
          },
        },
      })
    end,
  },

  -- https://github.com/akinsho/toggleterm.nvim
  {
    'akinsho/toggleterm.nvim',
    version = "*",
    keys = {
      { "<leader>t", "<cmd>ToggleTerm<cr>", desc = "Toggle Terminal" },
    },
    config = true
  },

  -- https://github.com/folke/which-key.nvim
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = {
      presets = "helix",
    },
    config = true,
  },

  -- https://github.com/echasnovski/mini.nvim/tree/main/readmes
  {
    'echasnovski/mini.nvim',
    version = false,
    config = function()
      require('mini.statusline').setup()
      require('mini.git').setup()
      require('mini.diff').setup()
    end,
  },
})
