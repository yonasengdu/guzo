import { Mail, Phone, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import Logo from './Logo';

export default function Footer() {
    return (
        <footer className="bg-white border-t border-gray-100">
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24 py-20">
                <div className="grid grid-cols-1 md:grid-cols-12 gap-16 mb-16">
                    {/* Brand Section */}
                    <div className="md:col-span-4">
                        <Logo size={40} className="mb-6" />
                        <p className="text-gray-600 text-sm leading-relaxed mb-6 max-w-sm">
                            Connecting Ethiopia through safe, reliable, and comfortable transportation. 
                            Your journey, elevated.
                        </p>
                        <div className="flex flex-col gap-3 text-sm text-gray-600">
                            <a
                                href="mailto:info@guzo.et"
                                className="flex items-center gap-3 hover:text-ethiopian-green transition-colors"
                            >
                                <Mail size={16} className="text-gray-400" />
                                info@guzo.et
                            </a>
                            <a
                                href="tel:+251900000000"
                                className="flex items-center gap-3 hover:text-ethiopian-green transition-colors"
                            >
                                <Phone size={16} className="text-gray-400" />
                                +251 900 00 00 00
                            </a>
                            <div className="flex items-start gap-3">
                                <MapPin size={16} className="text-gray-400 mt-0.5" />
                                <span>Addis Ababa, Ethiopia</span>
                            </div>
                        </div>
                    </div>

                    {/* Links Section */}
                    <div className="md:col-span-8 grid grid-cols-2 md:grid-cols-4 gap-12">
                        <div>
                            <h3 className="text-sm font-semibold text-gray-900 mb-4 uppercase tracking-wider">
                                Services
                            </h3>
                            <ul className="space-y-3">
                                <li>
                                    <Link
                                        to="/#services"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Private Charter
                                    </Link>
                                </li>
                                <li>
                                    <Link
                                        to="/#services"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Inter-City Rideshare
                                    </Link>
                                </li>
                                <li>
                                    <Link
                                        to="/#services"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Popular Routes
                                    </Link>
                                </li>
                                <li>
                                    <Link
                                        to="/signup"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Become a Driver
                                    </Link>
                                </li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-sm font-semibold text-gray-900 mb-4 uppercase tracking-wider">
                                Company
                            </h3>
                            <ul className="space-y-3">
                                <li>
                                    <Link
                                        to="/#trust"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        About Us
                                    </Link>
                                </li>
                                <li>
                                    <Link
                                        to="/#trust"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Safety & Trust
                                    </Link>
                                </li>
                                <li>
                                    <a
                                        href="#"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Careers
                                    </a>
                                </li>
                                <li>
                                    <a
                                        href="#"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Press
                                    </a>
                                </li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-sm font-semibold text-gray-900 mb-4 uppercase tracking-wider">
                                Legal
                            </h3>
                            <ul className="space-y-3">
                                <li>
                                    <a
                                        href="#"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Privacy Policy
                                    </a>
                                </li>
                                <li>
                                    <a
                                        href="#"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Terms of Service
                                    </a>
                                </li>
                                <li>
                                    <a
                                        href="#"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Cookie Policy
                                    </a>
                                </li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-sm font-semibold text-gray-900 mb-4 uppercase tracking-wider">
                                Connect
                            </h3>
                            <ul className="space-y-3">
                                <li>
                                    <a
                                        href="#"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Facebook
                                    </a>
                                </li>
                                <li>
                                    <a
                                        href="#"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Instagram
                                    </a>
                                </li>
                                <li>
                                    <a
                                        href="#"
                                        className="text-sm text-gray-600 hover:text-ethiopian-green transition-colors"
                                    >
                                        Twitter
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="pt-8 border-t border-gray-100">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                        <p className="text-xs text-gray-500">
                            &copy; {new Date().getFullYear()} Guzo Transport. All rights reserved.
                        </p>
                        <p className="text-xs text-gray-500">
                            Made with <span className="text-ethiopian-green">❤️</span> for Ethiopia
                        </p>
                    </div>
                </div>
            </div>
        </footer>
    );
}
