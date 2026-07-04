/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        charcoal: "#1B1F1D",
        panel: "#232823",
        moss: "#3F6B4E",
        lime: "#B8D93D",
        fog: "#C9D1C8",
      },
      fontFamily: {
        display: ["'Bebas Neue'", "Impact", "sans-serif"],
      },
    },
  },
  plugins: [],
};
