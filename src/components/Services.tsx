import { Car, Users, MapPin, Calendar, Shield, Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Service {
    title: string;
    description: string;
    icon: any;
    features: string[];
    cta: string;
    ctaLink: string;
    color: string;
    bgGradient: string;
    popular?: boolean;
}

const services: Service[] = [
    {
        title: 'Private Charter',
        description: 'Your personal mobility solution. Perfect for airport transfers, weddings, corporate needs, or family trips.',
        icon: Car,
        features: [
            'Dedicated car & driver',
            'Flexible scheduling',
            'Premium comfort',
            'Privacy guaranteed',
        ],
        cta: 'Book a Charter',
        ctaLink: '/signup',
        color: 'text-ethiopian-green',
        bgGradient: 'from-ethiopian-green/10 to-ethiopian-green/5',
    },
    {
        title: 'Inter-City Rideshare',
        description: 'Affordable, comfortable travel between major cities. Share the ride, split the cost, connect with fellow travelers.',
        icon: Users,
        features: [
            'Shared comfort',
            'Key routes covered',
            'Transparent pricing',
            'Book by seat or whole car',
        ],
        cta: 'Find a Ride',
        ctaLink: '/signup',
        color: 'text-ethiopian-gold',
        bgGradient: 'from-ethiopian-gold/10 to-ethiopian-gold/5',
        popular: true,
    },
];

const routes = [
    { from: 'Addis Ababa', to: 'Hawassa', distance: '275 km', time: '4-5 hours' },
    { from: 'Addis Ababa', to: 'Bahir Dar', distance: '565 km', time: '8-9 hours' },
    { from: 'Addis Ababa', to: 'Gondar', distance: '730 km', time: '10-11 hours' },
    { from: 'Addis Ababa', to: 'Adama', distance: '99 km', time: '1.5-2 hours' },
    { from: 'Addis Ababa', to: 'Dire Dawa', distance: '515 km', time: '7-8 hours' },
    { from: 'Hawassa', to: 'Addis Ababa', distance: '275 km', time: '4-5 hours' },
];

export default function Services() {
    return (
        <div id="services" className="py-32 bg-transparent">
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24">
                {/* Header */}
                <div className="mb-20">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-ethiopian-green/10 text-ethiopian-green font-semibold text-sm mb-4">
                        <MapPin size={16} />
                        Our Services
                    </div>
                    <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4 max-w-4xl">
                        Two Ways to <span className="text-gradient-ethiopian">Travel</span>
                    </h2>
                    <p className="text-xl text-gray-600 max-w-3xl">
                        Choose the service that fits your needs. From private charters to shared rides, we've got you covered.
                    </p>
                </div>

                {/* Services Cards */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-24">
                    {services.map((service, index) => {
                        const Icon = service.icon;
                        return (
                            <div
                                key={index}
                                className={`relative rounded-2xl p-8 bg-gradient-to-br ${service.bgGradient} border-2 border-gray-100 hover:border-opacity-30 transition-all duration-300 hover:shadow-2xl`}
                                style={{
                                    borderColor: index === 0 ? 'rgba(0, 135, 81, 0.1)' : 'rgba(252, 221, 9, 0.1)',
                                }}
                            >
                                {service.popular && (
                                    <div className="absolute top-6 right-6 px-3 py-1 bg-ethiopian-gold text-ethiopian-dark rounded-full text-xs font-bold">
                                        Most Popular
                                    </div>
                                )}

                                <div className={`${service.color} mb-6`}>
                                    <Icon size={48} />
                                </div>

                                <h3 className="text-3xl font-bold text-gray-900 mb-3">
                                    {service.title}
                                </h3>
                                <p className="text-lg text-gray-600 mb-6">
                                    {service.description}
                                </p>

                                <ul className="space-y-3 mb-8">
                                    {service.features.map((feature, i) => (
                                        <li key={i} className="flex items-center gap-3 text-gray-700">
                                            <div className={`w-2 h-2 rounded-full ${service.color.replace('text-', 'bg-')}`}></div>
                                            <span>{feature}</span>
                                        </li>
                                    ))}
                                </ul>

                                <Link
                                    to={service.ctaLink}
                                    className="inline-flex items-center gap-2 px-6 py-3 text-white rounded-lg font-semibold hover:opacity-90 transition-all duration-300 shadow-lg hover:shadow-xl"
                                    style={{
                                        backgroundColor: index === 0 ? '#008751' : '#FCDD09',
                                        color: index === 0 ? 'white' : '#1a1a1a',
                                    }}
                                >
                                    {service.cta}
                                    <ArrowRight size={20} />
                                </Link>
                            </div>
                        );
                    })}
                </div>

                {/* Popular Routes */}
                <div className="bg-gradient-to-br from-gray-50 to-ethiopian-green/5 rounded-2xl p-10 lg:p-16">
                    <div className="mb-12">
                        <h3 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4 max-w-3xl">
                            Popular <span className="text-gradient-ethiopian">Routes</span>
                        </h3>
                        <p className="text-lg text-gray-600 max-w-2xl">
                            Connecting major cities across Ethiopia
                        </p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {routes.map((route, index) => (
                            <div
                                key={index}
                                className="bg-white rounded-xl p-6 border border-gray-100 hover:border-ethiopian-green/30 hover:shadow-lg transition-all duration-300"
                            >
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                        <MapPin size={20} className="text-ethiopian-green" />
                                        <span className="font-semibold text-gray-900">{route.from}</span>
                                    </div>
                                    <ArrowRight size={16} className="text-gray-400" />
                                    <span className="font-semibold text-gray-900">{route.to}</span>
                                </div>
                                <div className="flex items-center gap-4 text-sm text-gray-600">
                                    <div className="flex items-center gap-1">
                                        <MapPin size={14} />
                                        <span>{route.distance}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Clock size={14} />
                                        <span>{route.time}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="text-center mt-8">
                        <p className="text-gray-600 mb-4">
                            Don't see your route? Request a custom trip and we'll match you with a driver.
                        </p>
                        <Link
                            to="/signup"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors"
                        >
                            Request Custom Route
                            <ArrowRight size={20} />
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
