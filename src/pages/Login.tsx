import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import Layout from '../components/Layout';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import Logo from '../components/Logo';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email,
                password,
            });

            if (error) throw error;

            // Check role and redirect
            if (data.user) {
                const { data: profile } = await supabase
                    .from('profiles')
                    .select('role')
                    .eq('id', data.user.id)
                    .single();

                if (profile?.role === 'admin') {
                    navigate('/admin');
                } else if (profile?.role === 'driver') {
                    navigate('/driver');
                } else if (profile?.role === 'customer') {
                    navigate('/customer');
                } else {
                    navigate('/customer');
                }
            }
        } catch (err: any) {
            setError(err.message);
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
                                Welcome Back
                            </h1>
                            <p className="text-lg text-gray-600">
                                Sign in to continue to your dashboard
                            </p>
                        </div>

                        {/* Login Form */}
                        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                            <form className="space-y-6" onSubmit={handleLogin}>
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
                                            placeholder="Enter your password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                        />
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
                                            <span>Signing in...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Sign In</span>
                                            <ArrowRight size={20} />
                                        </>
                                    )}
                                </button>
                            </form>

                            {/* Sign Up Link */}
                            <div className="mt-6 text-center">
                                <p className="text-sm text-gray-600">
                                    Don't have an account?{' '}
                                    <Link
                                        to="/signup"
                                        className="font-semibold text-ethiopian-green hover:text-ethiopian-green/80 transition-colors"
                                    >
                                        Sign up
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
