return {
  {
    "LazyVim/LazyVim",
    opts = function(_, opts)
      opts.colorscheme = "cyberdream"
    end,
  },
  {
    "ahmedkhalf/project.nvim",
    opts = {
      manual_mode = false,
    },
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
      opts.ensure_installed = "all"
    end,
  },
  {
    "scottmckendry/cyberdream.nvim",
  },
}
