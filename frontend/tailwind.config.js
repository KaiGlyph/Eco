/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'eco-purple': '#6A0DAD',
        'eco-purple-light': '#9D4EDD',
        'eco-dark': '#1A0033',
        'eco-gold': '#FFD700',
        'eco-gold-dark': '#FFA500',
        'eco-black': '#000000',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}