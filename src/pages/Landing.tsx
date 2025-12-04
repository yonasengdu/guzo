import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';
import Hero from '../components/Hero';
import Stats from '../components/Stats';
import Services from '../components/Services';
import Features from '../components/Features';
import Testimonials from '../components/Testimonials';
import Trust from '../components/Trust';
import Footer from '../components/Footer';

export default function Landing() {
    const { user, profile, loading } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        // Redirect authenticated users to their role-specific dashboard
        if (!loading && user && profile) {
            if (profile.role === 'admin') {
                navigate('/admin', { replace: true });
            } else if (profile.role === 'driver') {
                navigate('/driver', { replace: true });
            } else if (profile.role === 'customer') {
                navigate('/customer', { replace: true });
            }
        }
    }, [user, profile, loading, navigate]);

    // Show loading state while checking auth
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-primary"></div>
            </div>
        );
    }

    // If user is logged in, don't render landing (will redirect)
    if (user && profile) {
        return null;
    }

    return (
        <Layout>
            <Hero />
            <Stats />
            <Services />
            <Features />
            <Testimonials />
            <Trust />
            <Footer />
        </Layout>
    );
}
