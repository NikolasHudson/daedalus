/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './daedlaus/**/*.html',
    './daedlaus/**/*.js',
    './daedlaus/**/*.py',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: ["light", "dark", "cupcake", "business", "corporate"],
    darkTheme: "dark",
    logs: false
  },
}