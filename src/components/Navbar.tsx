import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';

export default function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const { user, profile, signOut } = useAuth();
    const location = useLocation();

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const isActive = (path: string) => location.pathname === path;

    return (
        <nav
            className={`fixed w-full z-50 transition-all duration-300 ${
                scrolled
                    ? 'bg-white/95 backdrop-blur-md shadow-sm'
                    : 'bg-white/80 backdrop-blur-sm'
            }`}
        >
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24">
                <div className="flex justify-between items-center h-20">
                    {/* Logo */}
                    <Link
                        to="/"
                        className="flex-shrink-0 flex items-center"
                        onClick={() => setIsOpen(false)}
                    >
                        <Logo size={36} />
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center gap-8">
                        <Link
                            to="/"
                            className={`text-sm font-medium transition-colors ${
                                isActive('/')
                                    ? 'text-ethiopian-green'
                                    : 'text-gray-700 hover:text-ethiopian-green'
                            }`}
                        >
                            Home
                        </Link>
                        <a
                            href="#services"
                            className="text-sm font-medium text-gray-700 hover:text-ethiopian-green transition-colors"
                        >
                            Services
                        </a>
                        <a
                            href="#trust"
                            className="text-sm font-medium text-gray-700 hover:text-ethiopian-green transition-colors"
                        >
                            Why Us
                        </a>

                        {user ? (
                            <div className="flex items-center gap-6 ml-4 pl-6 border-l border-gray-200">
                                {profile?.role === 'admin' && (
                                    <Link
                                        to="/admin"
                                        className={`text-sm font-medium transition-colors ${
                                            isActive('/admin')
                                                ? 'text-ethiopian-green'
                                                : 'text-gray-700 hover:text-ethiopian-green'
                                        }`}
                                    >
                                        Admin
                                    </Link>
                                )}
                                {profile?.role === 'driver' && (
                                    <Link
                                        to="/driver"
                                        className={`text-sm font-medium transition-colors ${
                                            isActive('/driver')
                                                ? 'text-ethiopian-green'
                                                : 'text-gray-700 hover:text-ethiopian-green'
                                        }`}
                                    >
                                        Driver
                                    </Link>
                                )}
                                {profile?.role === 'customer' && (
                                    <Link
                                        to="/customer"
                                        className={`text-sm font-medium transition-colors ${
                                            isActive('/customer')
                                                ? 'text-ethiopian-green'
                                                : 'text-gray-700 hover:text-ethiopian-green'
                                        }`}
                                    >
                                        My Bookings
                                    </Link>
                                )}
                                <button
                                    onClick={signOut}
                                    className="text-sm font-medium text-gray-700 hover:text-ethiopian-green transition-colors"
                                >
                                    Sign Out
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center gap-4 ml-4 pl-6 border-l border-gray-200">
                                <Link
                                    to="/login"
                                    className="text-sm font-medium text-gray-700 hover:text-ethiopian-green transition-colors"
                                >
                                    Login
                                </Link>
                                <Link
                                    to="/signup"
                                    className="px-4 py-2 bg-ethiopian-green text-white rounded-lg text-sm font-medium hover:bg-ethiopian-green/90 transition-all duration-200 shadow-sm hover:shadow-md"
                                >
                                    Sign Up
                                </Link>
                            </div>
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        onClick={() => setIsOpen(!isOpen)}
                        className="md:hidden inline-flex items-center justify-center p-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                        aria-label="Toggle menu"
                    >
                        {isOpen ? <X size={24} /> : <Menu size={24} />}
                    </button>
                </div>
            </div>

            {/* Mobile Menu */}
            {isOpen && (
                <div className="md:hidden border-t border-gray-200 bg-white/95 backdrop-blur-md">
                    <div className="px-4 pt-4 pb-6 space-y-1">
                        <Link
                            to="/"
                            className={`block px-4 py-3 rounded-lg text-base font-medium transition-colors ${
                                isActive('/')
                                    ? 'text-ethiopian-green bg-ethiopian-green/10'
                                    : 'text-gray-700 hover:bg-gray-50'
                            }`}
                            onClick={() => setIsOpen(false)}
                        >
                            Home
                        </Link>
                        <a
                            href="#services"
                            className="block px-4 py-3 rounded-lg text-base font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                            onClick={() => setIsOpen(false)}
                        >
                            Services
                        </a>
                        <a
                            href="#trust"
                            className="block px-4 py-3 rounded-lg text-base font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                            onClick={() => setIsOpen(false)}
                        >
                            Why Us
                        </a>

                        {user ? (
                            <>
                                {profile?.role === 'admin' && (
                                    <Link
                                        to="/admin"
                                        className={`block px-4 py-3 rounded-lg text-base font-medium transition-colors ${
                                            isActive('/admin')
                                                ? 'text-ethiopian-green bg-ethiopian-green/10'
                                                : 'text-gray-700 hover:bg-gray-50'
                                        }`}
                                        onClick={() => setIsOpen(false)}
                                    >
                                        Admin
                                    </Link>
                                )}
                                {profile?.role === 'driver' && (
                                    <Link
                                        to="/driver"
                                        className={`block px-4 py-3 rounded-lg text-base font-medium transition-colors ${
                                            isActive('/driver')
                                                ? 'text-ethiopian-green bg-ethiopian-green/10'
                                                : 'text-gray-700 hover:bg-gray-50'
                                        }`}
                                        onClick={() => setIsOpen(false)}
                                    >
                                        Driver
                                    </Link>
                                )}
                                {profile?.role === 'customer' && (
                                    <Link
                                        to="/customer"
                                        className={`block px-4 py-3 rounded-lg text-base font-medium transition-colors ${
                                            isActive('/customer')
                                                ? 'text-ethiopian-green bg-ethiopian-green/10'
                                                : 'text-gray-700 hover:bg-gray-50'
                                        }`}
                                        onClick={() => setIsOpen(false)}
                                    >
                                        My Bookings
                                    </Link>
                                )}
                                <button
                                    onClick={() => {
                                        signOut();
                                        setIsOpen(false);
                                    }}
                                    className="block w-full text-left px-4 py-3 rounded-lg text-base font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                                >
                                    Sign Out
                                </button>
                            </>
                        ) : (
                            <>
                                <Link
                                    to="/login"
                                    className="block px-4 py-3 rounded-lg text-base font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                                    onClick={() => setIsOpen(false)}
                                >
                                    Login
                                </Link>
                                <Link
                                    to="/signup"
                                    className="block px-4 py-3 rounded-lg text-base font-medium bg-ethiopian-green text-white hover:bg-ethiopian-green/90 transition-colors text-center"
                                    onClick={() => setIsOpen(false)}
                                >
                                    Sign Up
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            )}
        </nav>
    );
}
