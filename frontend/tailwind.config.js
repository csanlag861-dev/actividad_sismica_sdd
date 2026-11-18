/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      colors: {
        mars: {
          background: "var(--color-background)",
          surface: "var(--color-surface)",
          elevated: "var(--color-surface-elevated)",
          border: "var(--color-border)",
          text: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
          primary: "var(--color-primary)",
          accent: "var(--color-accent)"
        }
      }
    }
  },
  plugins: []
};
