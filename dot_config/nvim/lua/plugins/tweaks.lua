return {
  {
    "LazyVim/LazyVim",
    opts = function(_, opts)
      opts.colorscheme = "tokyonight-night"
    end,
  },
  {
    "ahmedkhalf/project.nvim",
    optional = true,
    opts = function(_, opts)
      opts.manual_mode = false
    end,
  },
  {
    "folke/trouble.nvim",
    opts = function(_, opts)
      opts.use_diagnostic_signs = true
    end,
  },
  {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      opts.auto_install = true
    end,
  },
}
