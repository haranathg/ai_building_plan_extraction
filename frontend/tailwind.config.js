/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'colab-navy': '#003d5c',
        'colab-teal': '#2b8a8e',
        'colab-orange': '#ff6b35',
        'colab-blue': '#2563eb',
      },
    },
  },
  plugins: [],
}
