import { ShieldCheck, Award, CheckCircle2 } from 'lucide-react';

const trustFeatures = [
    {
        icon: ShieldCheck,
        title: 'Verified & Vetted',
        description: 'All drivers undergo comprehensive background checks and vehicle inspections',
        color: 'text-ethiopian-green',
    },
    {
        icon: Award,
        title: 'Industry Certified',
        description: 'Compliant with Ethiopian transportation regulations and safety standards',
        color: 'text-ethiopian-gold',
    },
    {
        icon: CheckCircle2,
        title: 'Insured & Protected',
        description: 'Full insurance coverage for your peace of mind on every journey',
        color: 'text-ethiopian-red',
    },
];

export default function Trust() {
    return (
        <div id="trust" className="py-32 bg-transparent">
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24">
                <div className="mb-20">
                    <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4 max-w-4xl">
                        Travel with <span className="text-gradient-ethiopian">Confidence</span>
                    </h2>
                    <p className="text-xl text-gray-600 max-w-3xl">
                        We are not just a broker. We are your partner in mobility, ensuring a safe and pleasant journey every time.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-20">
                    {trustFeatures.map((feature, index) => {
                        const Icon = feature.icon;
                        return (
                            <div
                                key={index}
                                className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 text-center border border-gray-100"
                            >
                                <div className={`${feature.color} mb-4 flex justify-center`}>
                                    <Icon size={48} />
                                </div>
                                <h3 className="text-xl font-bold text-gray-900 mb-3">
                                    {feature.title}
                                </h3>
                                <p className="text-gray-600">
                                    {feature.description}
                                </p>
                            </div>
                        );
                    })}
                </div>

                {/* Trust Badges */}
                <div className="bg-white rounded-2xl p-10 shadow-lg border border-gray-100">
                    <div className="mb-10">
                        <h3 className="text-2xl font-bold text-gray-900 mb-2 max-w-3xl">
                            Why Thousands Trust Guzo
                        </h3>
                        <p className="text-gray-600 max-w-2xl">
                            Our commitment to safety, reliability, and customer satisfaction sets us apart
                        </p>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-ethiopian-green mb-2">100%</div>
                            <div className="text-sm text-gray-600">Verified Drivers</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-ethiopian-gold mb-2">24/7</div>
                            <div className="text-sm text-gray-600">Support Available</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-ethiopian-red mb-2">0</div>
                            <div className="text-sm text-gray-600">Hidden Fees</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-ethiopian-green mb-2">98%</div>
                            <div className="text-sm text-gray-600">On-Time Rate</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
