import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#16202a",
        panel: "#f8fafc",
        line: "#d8dee6",
        teal: "#0f766e",
        amber: "#b45309",
        rose: "#be123c"
      }
    }
  },
  plugins: []
};

export default config;
