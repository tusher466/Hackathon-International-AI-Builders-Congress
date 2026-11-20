/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        surfaceHover: "var(--surface-hover)",
        border: "var(--border)",
        borderHover: "var(--border-hover)",
        textPrimary: "var(--text-primary)",
        textMuted: "var(--text-muted)",
        accent: "var(--accent)",
        accentHover: "var(--accent-hover)",
        accentText: "var(--accent-text)",
        healthy: "var(--healthy)",
        warning: "var(--warning)",
        critical: "var(--critical)",
        offline: "var(--offline)",
        steel: "var(--steel)",
      },
      borderRadius: {
        card: "8px",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
