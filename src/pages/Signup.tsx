import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import Layout from '../components/Layout';
import { Mail, Lock, User, Phone, ArrowRight } from 'lucide-react';
import Logo from '../components/Logo';

export default function Signup() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [phone, setPhone] = useState('');
    const [role, setRole] = useState('customer');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        if (!phone || phone.trim() === '') {
            setError('Phone number is required');
            setLoading(false);
            return;
        }

        try {
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        full_name: fullName || 'User',
                        phone_number: phone.trim() || '0000000000',
                        role: role || 'customer',
                    },
                },
            });

            if (error) {
                console.error('Signup error:', error);
                throw error;
            }

            if (data.user) {
                // Wait a moment for the trigger to potentially create the profile
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Check if profile exists, if not create it manually (fallback)
                const { data: existingProfile } = await supabase
                    .from('profiles')
                    .select('id')
                    .eq('id', data.user.id)
                    .single();

                if (!existingProfile) {
                    // Profile doesn't exist, create it manually as fallback
                    console.log('Profile not found, creating manually as fallback...');
                    const { error: profileError } = await supabase
                        .from('profiles')
                        .insert([
                            {
                                id: data.user.id,
                                full_name: fullName || 'User',
                                phone_number: phone.trim() || '0000000000',
                                role: (role === 'driver' || role === 'admin' || role === 'customer') ? role : 'customer',
                            },
                        ]);

                    if (profileError) {
                        console.error('Error creating profile fallback:', profileError);
                        // Don't fail the signup, just log the error
                        // The user can still log in and we'll try again
                    } else {
                        console.log('Profile created successfully via fallback');
                    }
                }

                if (data.user.email_confirmed_at) {
                    alert('Signup successful! You can now log in.');
                    navigate('/login');
                } else {
                    alert('Signup successful! Please check your email for verification. If you don\'t see it, check your spam folder.');
                    navigate('/login');
                }
            } else {
                setError('Failed to create account. Please try again.');
            }
        } catch (err: any) {
            console.error('Signup error details:', err);
            if (err.message?.includes('phone_number') || err.message?.includes('null value')) {
                setError('Phone number is required. Please enter a valid phone number.');
            } else if (err.message?.includes('duplicate') || err.message?.includes('already registered')) {
                setError('This email is already registered. Please log in instead.');
            } else {
                setError(err.message || 'An error occurred during signup. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout>
            <div className="min-h-[calc(100vh-80px)] py-16 px-8 sm:px-12 lg:px-16 xl:px-24">
                <div className="max-w-[1600px] mx-auto">
                    <div className="max-w-md mx-auto">
                        {/* Logo and Header */}
                        <div className="mb-12">
                            <Logo size={48} className="mb-6" />
                            <h1 className="text-4xl font-bold text-gray-900 mb-3">
                                Create Your Account
                            </h1>
                            <p className="text-lg text-gray-600">
                                Join Guzo and start your journey today
                            </p>
                        </div>

                        {/* Signup Form */}
                        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                            <form className="space-y-5" onSubmit={handleSignup}>
                                {/* Full Name Field */}
                                <div>
                                    <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-2">
                                        Full Name
                                    </label>
                                    <div className="relative">
                                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                            <User size={20} className="text-gray-400" />
                                        </div>
                                        <input
                                            id="fullName"
                                            type="text"
                                            required
                                            className="block w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all duration-200 text-gray-900 placeholder-gray-400"
                                            placeholder="John Doe"
                                            value={fullName}
                                            onChange={(e) => setFullName(e.target.value)}
                                        />
                                    </div>
                                </div>

                                {/* Phone Number Field */}
                                <div>
                                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                                        Phone Number <span className="text-red-500">*</span>
                                    </label>
                                    <div className="relative">
                                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                            <Phone size={20} className="text-gray-400" />
                                        </div>
                                        <input
                                            id="phone"
                                            type="tel"
                                            required
                                            className="block w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all duration-200 text-gray-900 placeholder-gray-400"
                                            placeholder="+251 900 000 000"
                                            value={phone}
                                            onChange={(e) => setPhone(e.target.value)}
                                        />
                                    </div>
                                </div>

                                {/* Email Field */}
                                <div>
                                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                        Email Address
                                    </label>
                                    <div className="relative">
                                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                            <Mail size={20} className="text-gray-400" />
                                        </div>
                                        <input
                                            id="email"
                                            type="email"
                                            required
                                            className="block w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all duration-200 text-gray-900 placeholder-gray-400"
                                            placeholder="you@example.com"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                        />
                                    </div>
                                </div>

                                {/* Password Field */}
                                <div>
                                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                                        Password
                                    </label>
                                    <div className="relative">
                                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                            <Lock size={20} className="text-gray-400" />
                                        </div>
                                        <input
                                            id="password"
                                            type="password"
                                            required
                                            className="block w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all duration-200 text-gray-900 placeholder-gray-400"
                                            placeholder="Create a strong password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                        />
                                    </div>
                                </div>

                                {/* Role Selection */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-3">
                                        I want to be a:
                                    </label>
                                    <div className="grid grid-cols-2 gap-4">
                                        <label className={`relative flex items-center justify-center p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                                            role === 'customer'
                                                ? 'border-ethiopian-green bg-ethiopian-green/5'
                                                : 'border-gray-200 hover:border-gray-300'
                                        }`}>
                                            <input
                                                type="radio"
                                                value="customer"
                                                checked={role === 'customer'}
                                                onChange={(e) => setRole(e.target.value)}
                                                className="sr-only"
                                            />
                                            <div className="text-center">
                                                <div className="font-semibold text-gray-900">Customer</div>
                                                <div className="text-xs text-gray-500 mt-1">Book rides</div>
                                            </div>
                                        </label>
                                        <label className={`relative flex items-center justify-center p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                                            role === 'driver'
                                                ? 'border-ethiopian-green bg-ethiopian-green/5'
                                                : 'border-gray-200 hover:border-gray-300'
                                        }`}>
                                            <input
                                                type="radio"
                                                value="driver"
                                                checked={role === 'driver'}
                                                onChange={(e) => setRole(e.target.value)}
                                                className="sr-only"
                                            />
                                            <div className="text-center">
                                                <div className="font-semibold text-gray-900">Driver</div>
                                                <div className="text-xs text-gray-500 mt-1">Offer rides</div>
                                            </div>
                                        </label>
                                    </div>
                                </div>

                                {/* Error Message */}
                                {error && (
                                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                                        {error}
                                    </div>
                                )}

                                {/* Submit Button */}
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-ethiopian-green text-white rounded-lg font-semibold text-base hover:bg-ethiopian-green/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ethiopian-green transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? (
                                        <>
                                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                            <span>Creating account...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Create Account</span>
                                            <ArrowRight size={20} />
                                        </>
                                    )}
                                </button>
                            </form>

                            {/* Login Link */}
                            <div className="mt-6 text-center">
                                <p className="text-sm text-gray-600">
                                    Already have an account?{' '}
                                    <Link
                                        to="/login"
                                        className="font-semibold text-ethiopian-green hover:text-ethiopian-green/80 transition-colors"
                                    >
                                        Sign in
                                    </Link>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
}
