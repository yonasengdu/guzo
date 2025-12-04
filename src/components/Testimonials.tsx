import { Star, Quote } from 'lucide-react';

interface Testimonial {
    name: string;
    location: string;
    role: 'customer' | 'driver';
    rating: number;
    text: string;
    avatar?: string;
}

const testimonials: Testimonial[] = [
    {
        name: 'Alemayehu Bekele',
        location: 'Addis Ababa',
        role: 'customer',
        rating: 5,
        text: 'Guzo has transformed how I travel between cities. The shared rides are affordable, comfortable, and always on time. The drivers are professional and the booking process is so easy.',
    },
    {
        name: 'Meron Tadesse',
        location: 'Hawassa',
        role: 'customer',
        rating: 5,
        text: 'As a frequent traveler to Addis, Guzo has become my go-to service. The whole car booking option is perfect for my family trips. Safe, reliable, and great value for money.',
    },
    {
        name: 'Tewodros Gebre',
        location: 'Bahir Dar',
        role: 'driver',
        rating: 5,
        text: 'Being a Guzo driver has been life-changing. The platform is easy to use, I set my own schedule, and the support team is always helpful. My income has increased significantly.',
    },
    {
        name: 'Selamawit Hailu',
        location: 'Addis Ababa',
        role: 'customer',
        rating: 5,
        text: 'I love how transparent the pricing is. No surprises, no hidden fees. The app makes it so easy to find rides and book seats. Highly recommend to anyone traveling in Ethiopia.',
    },
    {
        name: 'Yonas Mekonnen',
        location: 'Gondar',
        role: 'driver',
        rating: 5,
        text: 'The best part about Guzo is the flexibility. I can create trips when I\'m going anyway, and passengers can book seats. It\'s a win-win for everyone. Great platform!',
    },
    {
        name: 'Hanna Assefa',
        location: 'Adama',
        role: 'customer',
        rating: 5,
        text: 'Safety was my biggest concern, but Guzo\'s vetting process gives me confidence. All drivers are verified and professional. I feel safe traveling with my children.',
    },
];

export default function Testimonials() {
    return (
        <div className="py-32 bg-transparent">
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24">
                <div className="mb-20">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-ethiopian-gold/10 text-ethiopian-gold font-semibold text-sm mb-4">
                        <Star size={16} className="fill-ethiopian-gold" />
                        Trusted by Thousands
                    </div>
                    <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4 max-w-4xl">
                        What Our <span className="text-gradient-ethiopian">Community</span> Says
                    </h2>
                    <p className="text-xl text-gray-600 max-w-3xl">
                        Real stories from real people across Ethiopia. See why thousands trust Guzo for their journeys.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                    {testimonials.map((testimonial, index) => (
                        <div
                            key={index}
                            className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 relative"
                        >
                            {/* Quote Icon */}
                            <div className="absolute top-6 right-6 text-ethiopian-green/10">
                                <Quote size={40} />
                            </div>

                            {/* Rating */}
                            <div className="flex gap-1 mb-4">
                                {[...Array(testimonial.rating)].map((_, i) => (
                                    <Star
                                        key={i}
                                        size={20}
                                        className="fill-ethiopian-gold text-ethiopian-gold"
                                    />
                                ))}
                            </div>

                            {/* Testimonial Text */}
                            <p className="text-gray-700 mb-6 leading-relaxed relative z-10">
                                "{testimonial.text}"
                            </p>

                            {/* Author Info */}
                            <div className="flex items-center gap-4 pt-6 border-t border-gray-100">
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-white ${
                                    testimonial.role === 'customer' 
                                        ? 'bg-ethiopian-green' 
                                        : 'bg-ethiopian-gold text-ethiopian-dark'
                                }`}>
                                    {testimonial.name.split(' ').map(n => n[0]).join('')}
                                </div>
                                <div>
                                    <div className="font-semibold text-gray-900">
                                        {testimonial.name}
                                    </div>
                                    <div className="text-sm text-gray-500 flex items-center gap-1">
                                        <span>{testimonial.location}</span>
                                        <span>•</span>
                                        <span className="capitalize">{testimonial.role}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Trust Badge */}
                <div className="mt-20">
                    <div className="inline-flex items-center gap-3 px-8 py-5 bg-white rounded-xl shadow-md border border-gray-100">
                        <div className="flex gap-1">
                            {[...Array(5)].map((_, i) => (
                                <Star
                                    key={i}
                                    size={24}
                                    className="fill-ethiopian-gold text-ethiopian-gold"
                                />
                            ))}
                        </div>
                        <div className="text-left">
                            <div className="font-bold text-gray-900">4.9/5 Average Rating</div>
                            <div className="text-sm text-gray-600">Based on 2,500+ reviews</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

