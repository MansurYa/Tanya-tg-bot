/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: '#1E1E2E',       // Deep Blue-Grey Background
        kusi: '#FF79C6',       // Neon Pink (Primary Currency)
        mint: '#50FA7B',       // Neon Green (Action/Success)
        tech: '#8BE9FD',       // Cyan (UI Borders/Icons)
        glass: 'rgba(30, 30, 46, 0.9)', // Glassmorphism panels
        textMain: '#F8F8F2',   // Off-white text
        textMuted: '#6272A4',  // Muted text
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'], // For numbers
        sans: ['Nunito', 'sans-serif'],        // For text
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      },
      backgroundColor: {
        glass: 'rgba(30, 30, 46, 0.7)',
      },
    },
  },
  plugins: [],
}