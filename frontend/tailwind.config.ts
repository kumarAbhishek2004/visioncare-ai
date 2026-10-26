import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        radDark: {
          950: "#07090e",
          900: "#0c1017",
          850: "#111722",
          800: "#161e2e",
          700: "#243048",
          600: "#334155",
        },
      },
    },
  },
  plugins: [],
};
export default config;
