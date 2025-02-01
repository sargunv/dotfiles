return {
  {
    -- https://github.com/LazyVim/LazyVim
    "LazyVim/LazyVim",
    opts = function(_, opts)
      opts.colorscheme = "tokyonight-night"
    end,
  },
  {
    -- https://github.com/ahmedkhalf/project.nvim
    "ahmedkhalf/project.nvim",
    optional = true,
    opts = function(_, opts)
      opts.manual_mode = false
    end,
  },
  {
    -- https://github.com/folke/trouble.nvim
    "folke/trouble.nvim",
    opts = function(_, opts)
      opts.use_diagnostic_signs = true
    end,
  },
  {
    -- https://github.com/nvim-treesitter/nvim-treesitter
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      opts.auto_install = true
    end,
  },
  {
    -- https://github.com/ThePrimeagen/vim-be-good
    "ThePrimeagen/vim-be-good",
  },
}
