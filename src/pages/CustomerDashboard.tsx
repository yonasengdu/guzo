import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { MapPin, Clock, Users, Plus, Search, Calendar, X, ArrowRight, CheckCircle2 } from 'lucide-react';
import { LOCATIONS } from '../constants/locations';

export default function CustomerDashboard() {
    const { user, profile } = useAuth();
    const [availableTrips, setAvailableTrips] = useState<any[]>([]);
    const [myBookings, setMyBookings] = useState<any[]>([]);
    const [showCustomRequest, setShowCustomRequest] = useState(false);
    const [activeTab, setActiveTab] = useState<'browse' | 'bookings'>('browse');

    const [filters, setFilters] = useState({
        origin: '',
        destination: '',
        date: '',
    });

    const [customRequest, setCustomRequest] = useState({
        pickup_location: '',
        dropoff_location: '',
        scheduled_time: '',
        seats_needed: '1',
        notes: '',
    });

    useEffect(() => {
        if (user) {
            fetchAvailableTrips();
            fetchMyBookings();
        }
    }, [user, filters]);

    const fetchAvailableTrips = async () => {
        let query = supabase
            .from('driver_trips')
            .select('*, profiles(full_name, phone_number)')
            .eq('status', 'scheduled')
            .gte('departure_time', new Date().toISOString());

        // Apply filters (exact match since we're using dropdowns)
        if (filters.origin) {
            query = query.eq('origin', filters.origin);
        }
        if (filters.destination) {
            query = query.eq('destination', filters.destination);
        }
        if (filters.date) {
            const startDate = new Date(filters.date);
            startDate.setHours(0, 0, 0, 0);
            const endDate = new Date(filters.date);
            endDate.setHours(23, 59, 59, 999);
            query = query.gte('departure_time', startDate.toISOString())
                .lte('departure_time', endDate.toISOString());
        }

        const { data } = await query.order('departure_time', { ascending: true });

        if (data) {
            setAvailableTrips(data.filter(trip => trip.available_seats > trip.booked_seats));
        }
    };

    const fetchMyBookings = async () => {
        if (!user) return;

        const { data } = await supabase
            .from('bookings')
            .select('*, driver_trips(*, profiles(full_name, phone_number)), profiles:assigned_driver_id(full_name, phone_number)')
            .eq('customer_id', user.id)
            .order('scheduled_time', { ascending: false });

        if (data) setMyBookings(data);
    };

    const handleCustomRequest = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user || !profile) return;

        const { error } = await supabase.from('bookings').insert([
            {
                customer_id: user.id,
                customer_name: profile.full_name,
                customer_phone: profile.phone_number,
                pickup_location: customRequest.pickup_location,
                dropoff_location: customRequest.dropoff_location,
                scheduled_time: customRequest.scheduled_time,
                booking_type: 'custom_request',
                seats_booked: parseInt(customRequest.seats_needed) || 1,
                status: 'pending',
                notes: customRequest.notes,
            },
        ]);

        if (!error) {
            setShowCustomRequest(false);
            setCustomRequest({
                pickup_location: '',
                dropoff_location: '',
                scheduled_time: '',
                seats_needed: '1',
                notes: '',
            });
            fetchMyBookings();
            alert('Booking request submitted! Admin will match you with a driver.');
        } else {
            alert('Error submitting request: ' + error.message);
        }
    };

    return (
        <Layout>
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24 py-12">
                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 mb-10">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-900 mb-2">Book a Ride</h1>
                        <p className="text-lg text-gray-600">Welcome back, {profile?.full_name}</p>
                    </div>
                    <button
                        onClick={() => setShowCustomRequest(true)}
                        className="flex items-center gap-2 px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-all duration-200 shadow-lg hover:shadow-xl"
                    >
                        <Plus size={20} />
                        Request Booking
                    </button>
                </div>

                {/* Tabs */}
                <div className="mb-8 border-b border-gray-200">
                    <nav className="flex space-x-8">
                        <button
                            onClick={() => setActiveTab('browse')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                                activeTab === 'browse'
                                    ? 'border-ethiopian-green text-ethiopian-green'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            Browse Trips
                        </button>
                        <button
                            onClick={() => setActiveTab('bookings')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                                activeTab === 'bookings'
                                    ? 'border-ethiopian-green text-ethiopian-green'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            My Bookings
                        </button>
                    </nav>
                </div>

                {/* Browse Trips Tab */}
                {activeTab === 'browse' && (
                    <div className="space-y-8">
                        {/* Filters */}
                        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                            <div className="flex items-center gap-2 mb-4">
                                <Search size={20} className="text-gray-400" />
                                <h3 className="text-lg font-semibold text-gray-900">Search Trips</h3>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div className="relative">
                                    <MapPin size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none z-10" />
                                    <select
                                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all bg-white appearance-none"
                                        value={filters.origin}
                                        onChange={e => setFilters({ ...filters, origin: e.target.value })}
                                    >
                                        <option value="">All Origins</option>
                                        {LOCATIONS.map((location) => (
                                            <option key={location} value={location}>
                                                {location}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div className="relative">
                                    <MapPin size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none z-10" />
                                    <select
                                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all bg-white appearance-none"
                                        value={filters.destination}
                                        onChange={e => setFilters({ ...filters, destination: e.target.value })}
                                    >
                                        <option value="">All Destinations</option>
                                        {LOCATIONS.map((location) => (
                                            <option key={location} value={location}>
                                                {location}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div className="relative">
                                    <Calendar size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                    <input
                                        type="date"
                                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                        value={filters.date}
                                        onChange={e => setFilters({ ...filters, date: e.target.value })}
                                    />
                                </div>
                                <button
                                    onClick={() => setFilters({ origin: '', destination: '', date: '' })}
                                    className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                                >
                                    Clear Filters
                                </button>
                            </div>
                        </div>

                        {/* Available Trips */}
                        {availableTrips.length === 0 ? (
                            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-16 text-center">
                                <MapPin size={48} className="mx-auto text-gray-300 mb-4" />
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">No trips available</h3>
                                <p className="text-gray-600 mb-6">Try adjusting your filters or request a booking.</p>
                                <button
                                    onClick={() => setShowCustomRequest(true)}
                                    className="px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors"
                                >
                                    Request Booking
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {availableTrips.map((trip) => {
                                    const availableSeats = trip.available_seats - trip.booked_seats;
                                    return (
                                        <div
                                            key={trip.id}
                                            className="bg-white rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300 overflow-hidden"
                                        >
                                            <div className="p-8">
                                                <div className="flex justify-between items-start mb-6">
                                                    <div className="flex-1">
                                                        <h3 className="text-2xl font-bold text-gray-900 mb-2">
                                                            {trip.origin} → {trip.destination}
                                                        </h3>
                                                        <div className="space-y-2 text-sm text-gray-600">
                                                            <div className="flex items-center gap-2">
                                                                <Clock size={16} className="text-gray-400" />
                                                                {new Date(trip.departure_time).toLocaleString()}
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <Users size={16} className="text-gray-400" />
                                                                Driver: {trip.profiles?.full_name}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="bg-ethiopian-green/10 text-ethiopian-green px-3 py-1 rounded-full text-sm font-semibold">
                                                        {availableSeats} seats
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                                                    <div>
                                                        <p className="text-xs text-gray-500 mb-1">Per Seat</p>
                                                        <p className="text-lg font-bold text-gray-900">{trip.price_per_seat} ETB</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-gray-500 mb-1">Whole Car</p>
                                                        <p className="text-lg font-bold text-gray-900">{trip.whole_car_price} ETB</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-gray-500 mb-1">Total Seats</p>
                                                        <p className="text-lg font-bold text-gray-900">{trip.available_seats}</p>
                                                    </div>
                                                </div>

                                                <div className="text-center py-4">
                                                    <p className="text-sm text-gray-600 mb-3">
                                                        Request a booking for this route
                                                    </p>
                                                    <button
                                                        onClick={() => setShowCustomRequest(true)}
                                                        className="px-6 py-2 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors"
                                                    >
                                                        Request Booking
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {/* My Bookings Tab */}
                {activeTab === 'bookings' && (
                    <div className="space-y-6">
                        {myBookings.length === 0 ? (
                            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-16 text-center">
                                <CheckCircle2 size={48} className="mx-auto text-gray-300 mb-4" />
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">No bookings yet</h3>
                                <p className="text-gray-600 mb-6">Browse available trips to book your first ride!</p>
                                <button
                                    onClick={() => setActiveTab('browse')}
                                    className="px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors"
                                >
                                    Browse Trips
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {myBookings.map((booking) => (
                                    <div
                                        key={booking.id}
                                        className="bg-white rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300"
                                    >
                                        <div className="p-8">
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="flex-1">
                                                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                                                        {booking.pickup_location} → {booking.dropoff_location}
                                                    </h3>
                                                    <div className="space-y-2 text-sm text-gray-600">
                                                        <div className="flex items-center gap-2">
                                                            <Clock size={16} className="text-gray-400" />
                                                            {new Date(booking.scheduled_time).toLocaleString()}
                                                        </div>
                                                        {booking.driver_trips && (
                                                            <div className="flex items-center gap-2">
                                                                <Users size={16} className="text-gray-400" />
                                                                {booking.driver_trips.profiles?.full_name} | {booking.driver_trips.profiles?.phone_number}
                                                            </div>
                                                        )}
                                                        {booking.profiles && (
                                                            <div className="flex items-center gap-2">
                                                                <Users size={16} className="text-gray-400" />
                                                                {booking.profiles.full_name} | {booking.profiles.phone_number}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                                                        booking.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                        booking.status === 'assigned' ? 'bg-blue-100 text-blue-800' :
                                                        'bg-yellow-100 text-yellow-800'
                                                    }`}>
                                                        {booking.status}
                                                    </span>
                                                    <p className="text-2xl font-bold text-gray-900 mt-3">
                                                        {booking.price} ETB
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 gap-4 pt-6 border-t border-gray-100">
                                                <div>
                                                    <p className="text-xs text-gray-500 uppercase mb-1">Booking Type</p>
                                                    <p className="text-sm font-semibold text-gray-900">
                                                        {booking.booking_type === 'whole_car' ? 'Whole Car' :
                                                            booking.booking_type === 'seat' ? `${booking.seats_booked} Seat(s)` :
                                                            'Custom Request'}
                                                    </p>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-500 uppercase mb-1">Pickup</p>
                                                    <p className="text-sm font-semibold text-gray-900">{booking.pickup_location}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Custom Request Modal */}
                {showCustomRequest && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                            <div className="p-8">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-2xl font-bold text-gray-900">Request Custom Trip</h3>
                                    <button
                                        onClick={() => setShowCustomRequest(false)}
                                        className="text-gray-400 hover:text-gray-600 transition-colors"
                                    >
                                        <X size={24} />
                                    </button>
                                </div>
                                <form onSubmit={handleCustomRequest} className="space-y-5">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Pickup Location</label>
                                        <select
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all bg-white"
                                            value={customRequest.pickup_location}
                                            onChange={e => setCustomRequest({ ...customRequest, pickup_location: e.target.value })}
                                            required
                                        >
                                            <option value="">Select pickup location</option>
                                            {LOCATIONS.map((location) => (
                                                <option key={location} value={location}>
                                                    {location}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Dropoff Location</label>
                                        <select
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all bg-white"
                                            value={customRequest.dropoff_location}
                                            onChange={e => setCustomRequest({ ...customRequest, dropoff_location: e.target.value })}
                                            required
                                        >
                                            <option value="">Select dropoff location</option>
                                            {LOCATIONS.map((location) => (
                                                <option key={location} value={location}>
                                                    {location}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Date & Time</label>
                                        <input
                                            type="datetime-local"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={customRequest.scheduled_time}
                                            onChange={e => setCustomRequest({ ...customRequest, scheduled_time: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Number of Seats Needed</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="20"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={customRequest.seats_needed}
                                            onChange={e => setCustomRequest({ ...customRequest, seats_needed: e.target.value })}
                                            required
                                        />
                                        <p className="text-xs text-gray-500 mt-1">How many seats do you need for this trip?</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Additional Notes (Optional)</label>
                                        <textarea
                                            placeholder="Any special requirements or notes..."
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all resize-none"
                                            value={customRequest.notes}
                                            onChange={e => setCustomRequest({ ...customRequest, notes: e.target.value })}
                                            rows={4}
                                        />
                                    </div>
                                    <div className="flex justify-end gap-3 pt-4">
                                        <button
                                            type="button"
                                            onClick={() => setShowCustomRequest(false)}
                                            className="px-6 py-3 text-gray-700 bg-gray-100 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            className="px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors shadow-lg hover:shadow-xl"
                                        >
                                            Submit Request
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
}
