import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          blue: "#177FC6",
          blueDark: "#0F6FAB",
          blueSoft: "#EAF3FB",
          grayLight: "#C7C6C6",
          grayMid: "#575756",
          black: "#1D1D1B",
          bg: "#F8FAFC",
        },
      },
      boxShadow: {
        soft: "0 8px 24px rgba(23, 127, 198, 0.08)",
        elevated: "0 12px 32px rgba(15, 23, 42, 0.08)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
    },
  },
  plugins: [],
};

export default config;
