import { ShieldCheck, Users, Clock, DollarSign, MapPin, Headphones } from 'lucide-react';

interface Feature {
    icon: any;
    title: string;
    description: string;
    color: string;
    bgColor: string;
}

const features: Feature[] = [
    {
        icon: ShieldCheck,
        title: 'Safety First',
        description: 'Every driver undergoes strict background checks, vehicle inspections, and continuous monitoring. Your safety is our top priority.',
        color: 'text-ethiopian-green',
        bgColor: 'bg-ethiopian-green/10',
    },
    {
        icon: Users,
        title: 'Vetted Drivers',
        description: 'Our professional drivers are carefully selected, trained, and verified. Experience reliable service with friendly, knowledgeable drivers.',
        color: 'text-ethiopian-gold',
        bgColor: 'bg-ethiopian-gold/10',
    },
    {
        icon: Clock,
        title: 'Punctual & Reliable',
        description: 'We value your time. Our drivers are punctual and committed to getting you to your destination on schedule, every time.',
        color: 'text-ethiopian-red',
        bgColor: 'bg-ethiopian-red/10',
    },
    {
        icon: DollarSign,
        title: 'Transparent Pricing',
        description: 'No hidden fees, no surprises. Clear, upfront pricing for all routes. Book with confidence knowing exactly what you\'ll pay.',
        color: 'text-ethiopian-green',
        bgColor: 'bg-ethiopian-green/10',
    },
    {
        icon: MapPin,
        title: 'Wide Coverage',
        description: 'Connecting major cities across Ethiopia. From Addis Ababa to Hawassa, Bahir Dar, Gondar, and beyond.',
        color: 'text-ethiopian-gold',
        bgColor: 'bg-ethiopian-gold/10',
    },
    {
        icon: Headphones,
        title: '24/7 Support',
        description: 'Our support team is always available to help. Whether you need to modify a booking or have questions, we\'re here for you.',
        color: 'text-ethiopian-red',
        bgColor: 'bg-ethiopian-red/10',
    },
];

export default function Features() {
    return (
        <div className="py-32 bg-transparent">
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24">
                <div className="mb-20">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-ethiopian-green/10 text-ethiopian-green font-semibold text-sm mb-4">
                        Why Choose Guzo
                    </div>
                    <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4 max-w-4xl">
                        Everything You Need for a <span className="text-gradient-ethiopian">Perfect Journey</span>
                    </h2>
                    <p className="text-xl text-gray-600 max-w-3xl">
                        We've built Guzo with your comfort, safety, and convenience in mind. 
                        Experience the difference of a service designed for Ethiopia.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                    {features.map((feature, index) => {
                        const Icon = feature.icon;
                        return (
                            <div
                                key={index}
                                className="group p-8 rounded-2xl border border-gray-100 hover:border-ethiopian-green/30 hover:shadow-xl transition-all duration-300 bg-white"
                            >
                                <div className={`${feature.bgColor} ${feature.color} w-16 h-16 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                                    <Icon size={32} />
                                </div>
                                <h3 className="text-xl font-bold text-gray-900 mb-3">
                                    {feature.title}
                                </h3>
                                <p className="text-gray-600 leading-relaxed">
                                    {feature.description}
                                </p>
                            </div>
                        );
                    })}
                </div>

                {/* CTA Section */}
                <div className="mt-20">
                    <div className="max-w-4xl p-10 rounded-2xl bg-gradient-ethiopian-subtle border border-ethiopian-green/20">
                        <h3 className="text-2xl font-bold text-gray-900 mb-2">
                            Ready to Experience Guzo?
                        </h3>
                        <p className="text-gray-600 mb-6">
                            Join thousands of satisfied travelers across Ethiopia
                        </p>
                        <a
                            href="/signup"
                            className="inline-flex items-center gap-2 px-8 py-4 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors shadow-lg hover:shadow-xl"
                        >
                            Get Started Today
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}

