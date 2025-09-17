/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#1f2937',
          accent: '#0ea5e9'
        }
      }
    }
  },
  plugins: []
};
