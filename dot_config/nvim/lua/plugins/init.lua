return {
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    opts = {
      indent = { enable = true },
    },
    config = function(_, opts)
      require("nvim-treesitter.configs").setup(opts)
    end,
  },
  {
    "akinsho/toggleterm.nvim",
    opts = {
      direction = "float",
      open_mapping = [[<C-\>]],
      float_opts = { border = "curved" },
    },
  },
  {
    "nvim-telescope/telescope.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
      { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
    },
    keys = {
      { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find files" },
      { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Live grep" },
      { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "Buffers" },
      { "<leader>fh", "<cmd>Telescope help_tags<cr>", desc = "Help tags" },
      { "<leader>fd", "<cmd>Telescope diagnostics<cr>", desc = "Diagnostics" },
      { "<leader>fr", "<cmd>Telescope lsp_references<cr>", desc = "LSP references" },
      { "<leader>fs", "<cmd>Telescope lsp_document_symbols<cr>", desc = "Document symbols" },
    },
    config = function()
      require("telescope").setup()
      pcall(require("telescope").load_extension, "fzf")
    end,
  },
  {
    "nvim-neo-tree/neo-tree.nvim",
    branch = "v3.x",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "MunifTanjim/nui.nvim",
      "echasnovski/mini.icons",
    },
    keys = {
      { "<leader>e", "<cmd>Neotree toggle<cr>", desc = "Toggle file explorer" },
    },
    opts = {
      filesystem = {
        follow_current_file = { enabled = true },
        filtered_items = {
          visible = true,
          hide_dotfiles = false,
          hide_gitignored = false,
        },
      },
    },
  },
  { "nvim-lualine/lualine.nvim", opts = {} },
  {
    "akinsho/bufferline.nvim",
    dependencies = "echasnovski/mini.nvim",
    keys = {
      { "<S-l>", "<cmd>BufferLineCycleNext<cr>", desc = "Next buffer" },
      { "<S-h>", "<cmd>BufferLineCyclePrev<cr>", desc = "Previous buffer" },
      { "<leader>bd", function() require("mini.bufremove").delete() end, desc = "Delete buffer" },
    },
    opts = {
      options = {
        diagnostics = "nvim_lsp",
        close_command = function(bufnum)
          require("mini.bufremove").delete(bufnum, false)
        end,
        offsets = {
          {
            filetype = "neo-tree",
            text = "File Explorer",
            highlight = "Directory",
            separator = true,
          },
        },
      },
    },
  },
  { "lukas-reineke/indent-blankline.nvim", main = "ibl", opts = {} },
  {
    "lewis6991/gitsigns.nvim",
    keys = {
      { "<leader>gb", "<cmd>Gitsigns blame_line<cr>", desc = "Blame line" },
      { "<leader>gp", "<cmd>Gitsigns preview_hunk<cr>", desc = "Preview hunk" },
      { "<leader>gr", "<cmd>Gitsigns reset_hunk<cr>", desc = "Reset hunk" },
      { "<leader>gs", "<cmd>Gitsigns stage_hunk<cr>", desc = "Stage hunk" },
      { "]c", "<cmd>Gitsigns next_hunk<cr>", desc = "Next hunk" },
      { "[c", "<cmd>Gitsigns prev_hunk<cr>", desc = "Previous hunk" },
    },
    opts = {
      current_line_blame = true,
    },
  },
  {
    "stevearc/conform.nvim",
    keys = {
      {
        "<leader>lf",
        function() require("conform").format({ lsp_format = "fallback" }) end,
        desc = "Format buffer",
      },
    },
    opts = {
      format_on_save = {
        timeout_ms = 500,
        lsp_format = "fallback",
      },
      formatters_by_ft = {
        javascript = { "dprint" },
        typescript = { "dprint" },
        javascriptreact = { "dprint" },
        typescriptreact = { "dprint" },
        json = { "dprint" },
        markdown = { "dprint" },
        toml = { "dprint" },
        css = { "dprint" },
        html = { "dprint" },
        yaml = { "dprint" },
      },
    },
  },
  {
    "mfussenegger/nvim-lint",
    config = function()
      require("lint").linters_by_ft = {
        javascript = { "oxlint" },
        typescript = { "oxlint" },
        javascriptreact = { "oxlint" },
        typescriptreact = { "oxlint" },
      }
      vim.api.nvim_create_autocmd("BufWritePost", {
        callback = function()
          require("lint").try_lint()
        end,
      })
    end,
  },
  {
    "saghen/blink.cmp",
    version = "*",
    opts = {
      appearance = { nerd_font_variant = "normal" },
      signature = { enabled = true },
    },
  },
  {
    "williamboman/mason.nvim",
    opts = {},
  },
  {
    "williamboman/mason-lspconfig.nvim",
    dependencies = {
      "williamboman/mason.nvim",
      "neovim/nvim-lspconfig",
      "saghen/blink.cmp",
    },
    opts = {
      ensure_installed = {
        "bashls",
        "clangd",
        "cssls",
        "dockerls",
        "gopls",
        "html",
        "jsonls",
        "lua_ls",
        "pyright",
        "rust_analyzer",
        "tailwindcss",
        "taplo",
        "terraformls",
        "ts_ls",
        "yamlls",
      },
    },
    config = function(_, opts)
      require("mason").setup()
      require("mason-lspconfig").setup(opts)

      local capabilities = require("blink.cmp").get_lsp_capabilities()
      local lspconfig = require("lspconfig")

      vim.lsp.inlay_hint.enable(true)

      for _, server in ipairs(opts.ensure_installed) do
        lspconfig[server].setup({ capabilities = capabilities })
      end
    end,
  },
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    dependencies = "williamboman/mason.nvim",
    opts = {
      ensure_installed = {
        "dprint",
        "oxlint",
      },
    },
  },
  {
    "echasnovski/mini.nvim",
    config = function()
      require("mini.bufremove").setup()
      require("mini.icons").setup()
      require("mini.pairs").setup()
      MiniIcons.mock_nvim_web_devicons()
    end,
  },
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = {
      spec = {
        { "<leader>f", group = "Find" },
        { "<leader>g", group = "Git" },
        { "<leader>l", group = "LSP" },
        { "<leader>b", group = "Buffer" },
      },
    },
    keys = {
      { "<leader>la", function() vim.lsp.buf.code_action() end, desc = "Code action" },
      { "<leader>lr", function() vim.lsp.buf.rename() end, desc = "Rename symbol" },
      { "<leader>tg", function()
        require("toggleterm.terminal").Terminal:new({ cmd = "lazygit", direction = "float" }):toggle()
      end, desc = "Lazygit" },
      { "<Esc>", "<cmd>nohlsearch<cr>", mode = "n", desc = "Clear search highlight" },
    },
  },
  {
    "cursortab/cursortab.nvim",
    lazy = false,
    build = "cd server && go build",
    opts = {
      provider = {
        type = "mercuryapi",
        api_key_env = "INCEPTION_API_KEY",
      },
    },
  },
}
