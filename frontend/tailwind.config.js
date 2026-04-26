/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        header: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        'amber-gold': {
          DEFAULT: '#fbbf24',
          hover: '#f59e0b',
          light: '#fef3c7',
          dark: '#92400e',
        },
        'obsidian': {
          DEFAULT: '#000000',
          card: '#0a0a0a',
          glass: 'rgba(10, 10, 10, 0.85)',
        }
      },
      boxShadow: {
        'glow': '0 0 40px 10px rgba(251, 191, 36, 0.1)',
        'glow-hover': '0 0 50px 15px rgba(251, 191, 36, 0.2)',
        'edge-light': '0 0 30px 5px rgba(217, 119, 6, 0.08)',
      }
    },
  },
  plugins: [],
}
