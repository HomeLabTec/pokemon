/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"] ,
  theme: {
    extend: {
      colors: {
        base: "#0b0f0d",
        surface: "#111a16",
        accent: "#3aff7a",
      },
    },
  },
  plugins: [],
};
