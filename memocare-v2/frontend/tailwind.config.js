/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'display': ['"Dela Gothic One"', 'cursive'],
        'mono': ['"Space Mono"', 'monospace'],
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        card: {
          DEFAULT: "rgba(255, 255, 255, 0.05)",
          foreground: "hsl(var(--card-foreground))",
        },
        // Dashboard theme colors
        'cream': '#f5f5f0',
        'ink': '#1a1a1a',
        'ink-light': '#555555',
        'mri-cyan': '#06b6d4',
        'assess-amber': '#f59e0b',
        'page-dark': '#0a0a0c',
      },
      animation: {
        "float": "float 6s ease-in-out infinite",
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        }
      }
    },
  },
  plugins: [require("tailwindcss-animate")],
}
