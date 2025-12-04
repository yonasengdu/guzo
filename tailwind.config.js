/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                brand: {
                    primary: '#008751', // Ethiopian Flag Green
                    secondary: '#FCDD09', // Ethiopian Flag Yellow/Gold
                    accent: '#DA1212', // Ethiopian Flag Red
                    dark: '#1a1a1a',
                    light: '#f8f9fa',
                },
                ethiopian: {
                    green: '#008751',
                    gold: '#FCDD09',
                    red: '#DA1212',
                    dark: '#1a1a1a',
                    light: '#f8f9fa',
                }
            },
            fontFamily: {
                sans: ['Inter', 'Poppins', 'system-ui', 'sans-serif'],
                display: ['Poppins', 'Inter', 'system-ui', 'sans-serif'],
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-in',
                'slide-up': 'slideUp 0.5s ease-out',
                'slide-in-right': 'slideInRight 0.5s ease-out',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                slideInRight: {
                    '0%': { transform: 'translateX(-20px)', opacity: '0' },
                    '100%': { transform: 'translateX(0)', opacity: '1' },
                },
            },
            backgroundImage: {
                'gradient-ethiopian': 'linear-gradient(135deg, #008751 0%, #FCDD09 50%, #DA1212 100%)',
                'gradient-ethiopian-subtle': 'linear-gradient(135deg, rgba(0, 135, 81, 0.1) 0%, rgba(252, 221, 9, 0.1) 50%, rgba(218, 18, 18, 0.1) 100%)',
            },
        },
    },
    plugins: [],
}
