import { ArrowRight, Play, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Hero() {
    return (
        <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
            {/* Background with overlay */}
            <div className="absolute inset-0 z-0">
                <img
                    className="w-full h-full object-cover"
                    src="/assets/hero-bg.png"
                    alt="Beautiful Ethiopian landscape"
                />
                <div className="absolute inset-0 bg-gradient-to-br from-ethiopian-green/90 via-ethiopian-green/80 to-ethiopian-dark/90" />
                <div className="absolute inset-0 bg-pattern-ethiopian" />
            </div>

            {/* Content */}
            <div className="relative z-10 max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24 py-32">
                <div className="animate-fade-in">
                    {/* Badge */}
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-8 animate-slide-up">
                        <MapPin size={16} className="text-ethiopian-gold" />
                        <span className="text-sm font-medium text-white">Connecting Ethiopia, One Journey at a Time</span>
                    </div>

                    {/* Main Heading */}
                    <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                        <span className="block">Your Journey,</span>
                        <span className="block text-gradient-ethiopian bg-clip-text text-transparent bg-gradient-to-r from-ethiopian-gold via-ethiopian-gold to-ethiopian-red">
                            Elevated.
                        </span>
                    </h1>

                    {/* Subheading */}
                    <p className="text-xl sm:text-2xl text-gray-100 max-w-4xl mb-12 leading-relaxed animate-slide-up" style={{ animationDelay: '0.2s' }}>
                        Experience Ethiopia with safety, comfort, and reliability. 
                        <span className="block mt-2 text-lg text-gray-200">
                            Whether it's a private charter or a shared inter-city ride, Guzo connects you to your destination.
                        </span>
                    </p>

                    {/* CTAs */}
                    <div className="flex flex-col sm:flex-row items-start gap-4 mb-16 animate-slide-up" style={{ animationDelay: '0.3s' }}>
                        <Link
                            to="/signup"
                            className="group flex items-center justify-center gap-2 px-8 py-4 bg-ethiopian-gold text-ethiopian-dark rounded-lg font-semibold text-lg shadow-xl hover:bg-ethiopian-gold/90 hover:scale-105 transition-all duration-300"
                        >
                            Book Your Ride
                            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <a
                            href="#services"
                            className="flex items-center justify-center gap-2 px-8 py-4 bg-white/10 backdrop-blur-sm text-white rounded-lg font-semibold text-lg border border-white/20 hover:bg-white/20 transition-all duration-300"
                        >
                            <Play size={20} />
                            Learn More
                        </a>
                    </div>

                    {/* Stats Preview */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-10 max-w-5xl animate-slide-up" style={{ animationDelay: '0.4s' }}>
                        <div className="text-center">
                            <div className="text-3xl sm:text-4xl font-bold text-ethiopian-gold mb-2">10K+</div>
                            <div className="text-sm text-gray-300">Rides Completed</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl sm:text-4xl font-bold text-ethiopian-gold mb-2">25+</div>
                            <div className="text-sm text-gray-300">Cities Connected</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl sm:text-4xl font-bold text-ethiopian-gold mb-2">500+</div>
                            <div className="text-sm text-gray-300">Verified Drivers</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl sm:text-4xl font-bold text-ethiopian-gold mb-2">98%</div>
                            <div className="text-sm text-gray-300">Satisfaction Rate</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Scroll Indicator */}
            <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10 animate-bounce">
                <div className="w-6 h-10 border-2 border-white/30 rounded-full flex items-start justify-center p-2">
                    <div className="w-1 h-3 bg-white/50 rounded-full"></div>
                </div>
            </div>
        </div>
    );
}
