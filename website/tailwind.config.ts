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
        canvas: "#F0F0F0",
        ink: "#121212",
        red: {
          DEFAULT: "#D02020",
          soft: "#F6D4D4",
        },
        blue: {
          DEFAULT: "#1040C0",
          soft: "#D4DCF5",
        },
        yellow: {
          DEFAULT: "#F0C020",
          soft: "#FBEBC0",
        },
        muted: "#E0E0E0",
      },
      fontFamily: {
        outfit: ["var(--font-outfit)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        hard: "4px 4px 0 0 #121212",
        "hard-sm": "3px 3px 0 0 #121212",
        "hard-md": "6px 6px 0 0 #121212",
        "hard-lg": "8px 8px 0 0 #121212",
      },
    },
  },
  plugins: [],
};
export default config;
