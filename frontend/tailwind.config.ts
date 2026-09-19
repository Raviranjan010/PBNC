import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F7F9FC",
        surface: "#FFFFFF",
        border: "#E4E8EF",
        primary: {
          DEFAULT: "#1769E0",
          dark: "#0E4FA8",
          light: "#EBF3FE",
        },
        text: {
          DEFAULT: "#172033",
          muted: "#687386",
        },
        success: {
          DEFAULT: "#16865B",
          light: "#E8F5EF",
        },
        warning: {
          DEFAULT: "#D98A00",
          light: "#FDF5E6",
        },
        danger: {
          DEFAULT: "#D64545",
          light: "#FDF1F1",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        card: "0 2px 5px 0 rgba(23, 32, 51, 0.04), 0 1px 2px 0 rgba(23, 32, 51, 0.02)",
        elevation: "0 10px 25px -5px rgba(23, 32, 51, 0.08), 0 8px 10px -6px rgba(23, 32, 51, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
