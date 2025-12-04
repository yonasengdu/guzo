import Navbar from './Navbar';

interface LayoutProps {
    children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-ethiopian-gold/10 via-white to-ethiopian-green/10">
            <Navbar />
            <main className="pt-20">
                {children}
            </main>
        </div>
    );
}
