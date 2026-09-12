/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#1F3864',
          mid: '#2E75B6',
          light: '#D9EAF7',
          total: '#BDD7EE',
        },
      },
    },
  },
  plugins: [],
}
