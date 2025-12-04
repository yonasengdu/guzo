interface LogoProps {
    className?: string;
    size?: number;
    showText?: boolean;
}

export default function Logo({ className = '', size = 32, showText = true }: LogoProps) {
    return (
        <div className={`flex items-center gap-2 ${className}`}>
            {/* Modern minimalist logo - Ethiopian-inspired geometric design */}
            <svg
                width={size}
                height={size}
                viewBox="0 0 40 40"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="flex-shrink-0"
            >
                {/* Ethiopian-inspired geometric pattern - represents movement/journey */}
                <circle cx="20" cy="20" r="18" fill="#008751" opacity="0.1" />
                <path
                    d="M20 2 L26 14 L38 20 L26 26 L20 38 L14 26 L2 20 L14 14 Z"
                    fill="#008751"
                    stroke="#FCDD09"
                    strokeWidth="1.5"
                />
                <circle cx="20" cy="20" r="6" fill="#FCDD09" />
                <circle cx="20" cy="20" r="3" fill="#008751" />
            </svg>
            {showText && (
                <span className="font-display font-bold text-xl text-gray-900 tracking-tight">
                    Guzo
                </span>
            )}
        </div>
    );
}

