import { useEffect, useRef, useState } from 'react';
import { Users, MapPin, Car, Star } from 'lucide-react';

interface StatItem {
    icon: any;
    value: number;
    suffix: string;
    label: string;
    color: string;
}

const stats: StatItem[] = [
    {
        icon: Users,
        value: 10000,
        suffix: '+',
        label: 'Happy Customers',
        color: 'text-ethiopian-green',
    },
    {
        icon: MapPin,
        value: 25,
        suffix: '+',
        label: 'Cities Connected',
        color: 'text-ethiopian-gold',
    },
    {
        icon: Car,
        value: 500,
        suffix: '+',
        label: 'Verified Drivers',
        color: 'text-ethiopian-red',
    },
    {
        icon: Star,
        value: 98,
        suffix: '%',
        label: 'Satisfaction Rate',
        color: 'text-ethiopian-green',
    },
];

function useCountUp(end: number, duration: number = 2000, suffix: string = '') {
    const [count, setCount] = useState(0);
    const [isVisible, setIsVisible] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting && !isVisible) {
                    setIsVisible(true);
                }
            },
            { threshold: 0.5 }
        );

        if (ref.current) {
            observer.observe(ref.current);
        }

        return () => {
            if (ref.current) {
                observer.unobserve(ref.current);
            }
        };
    }, [isVisible]);

    useEffect(() => {
        if (!isVisible) return;

        let startTime: number | null = null;
        const animate = (currentTime: number) => {
            if (startTime === null) startTime = currentTime;
            const progress = Math.min((currentTime - startTime) / duration, 1);
            
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            setCount(Math.floor(easeOutQuart * end));

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                setCount(end);
            }
        };

        requestAnimationFrame(animate);
    }, [isVisible, end, duration]);

    return { count, ref };
}

export default function Stats() {
    return (
        <div className="py-32 bg-transparent">
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24">
                <div className="mb-20">
                    <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4 max-w-4xl">
                        Trusted by Thousands Across <span className="text-gradient-ethiopian">Ethiopia</span>
                    </h2>
                    <p className="text-xl text-gray-600 max-w-3xl">
                        Our numbers speak for themselves. Join the growing community of satisfied travelers.
                    </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
                    {stats.map((stat, index) => {
                        const { count, ref } = useCountUp(stat.value, 2000, stat.suffix);
                        const Icon = stat.icon;

                        return (
                            <div
                                key={index}
                                ref={ref}
                                className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 border border-gray-100"
                            >
                                <div className={`${stat.color} mb-4`}>
                                    <Icon size={48} className="opacity-80" />
                                </div>
                                <div className="mb-2">
                                    <span className="text-4xl sm:text-5xl font-bold text-gray-900">
                                        {count.toLocaleString()}
                                    </span>
                                    <span className="text-2xl font-bold text-ethiopian-gold ml-1">
                                        {stat.suffix}
                                    </span>
                                </div>
                                <div className="text-gray-600 font-medium">{stat.label}</div>
                            </div>
                        );
                    })}
                </div>

                {/* Additional Info */}
                <div className="mt-16 text-center">
                    <div className="inline-flex items-center gap-2 px-6 py-3 bg-ethiopian-green/10 rounded-full">
                        <div className="w-2 h-2 bg-ethiopian-green rounded-full animate-pulse"></div>
                        <span className="text-sm font-medium text-gray-700">
                            Growing every day • Real-time updates
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

