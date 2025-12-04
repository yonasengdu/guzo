import React, { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import Layout from '../components/Layout';
import { Plus, User, Calendar, Edit, Filter, Link as LinkIcon, DollarSign, X, Phone, MapPin, Clock, Users, CheckCircle2 } from 'lucide-react';
import { LOCATIONS } from '../constants/locations';

export default function AdminDashboard() {
    const [bookings, setBookings] = useState<any[]>([]);
    const [customRequests, setCustomRequests] = useState<any[]>([]);
    const [driverTrips, setDriverTrips] = useState<any[]>([]);
    const [drivers, setDrivers] = useState<any[]>([]);
    const [showNewBooking, setShowNewBooking] = useState(false);
    const [activeTab, setActiveTab] = useState<'trips' | 'custom-requests' | 'all-bookings'>('trips');
    const [editingPrice, setEditingPrice] = useState<{ tripId: string; field: 'price_per_seat' | 'whole_car_price' } | null>(null);
    const [matchingRequest, setMatchingRequest] = useState<string | null>(null);
    const [matchingSeats, setMatchingSeats] = useState<{ [key: string]: number }>({});

    const [filters, setFilters] = useState({
        date: '',
        driver: '',
        status: '',
    });

    const [newBooking, setNewBooking] = useState({
        customer_name: '',
        customer_phone: '',
        pickup_location: '',
        dropoff_location: '',
        scheduled_time: '',
        price: '',
        assigned_driver_id: '',
        booking_type: 'custom_request' as 'seat' | 'whole_car' | 'custom_request',
    });

    useEffect(() => {
        fetchData();
    }, [filters]);

    const fetchData = async () => {
        // Fetch all bookings for admin view
        let bookingsQuery = supabase
            .from('bookings')
            .select('*, profiles(full_name), driver_trips(*, profiles(full_name))')
            .order('created_at', { ascending: false });

        if (filters.date) {
            const startDate = new Date(filters.date);
            startDate.setHours(0, 0, 0, 0);
            const endDate = new Date(filters.date);
            endDate.setHours(23, 59, 59, 999);
            bookingsQuery = bookingsQuery
                .gte('scheduled_time', startDate.toISOString())
                .lte('scheduled_time', endDate.toISOString());
        }

        const { data: bookingsData, error: bookingsError } = await bookingsQuery;
        
        if (bookingsError) {
            console.error('Error fetching bookings:', bookingsError);
        }
        
        if (bookingsData) {
            setBookings(bookingsData);
            // Filter for pending custom requests - ensure we get all of them
            const pendingRequests = bookingsData.filter(b => 
                b.booking_type === 'custom_request' && 
                b.status === 'pending' &&
                !b.driver_trip_id // Not yet assigned to a trip
            );
            setCustomRequests(pendingRequests);
        }

        let tripsQuery = supabase
            .from('driver_trips')
            .select('*, profiles(full_name, phone_number), bookings(*)')
            .order('departure_time', { ascending: true });

        if (filters.driver) {
            tripsQuery = tripsQuery.eq('driver_id', filters.driver);
        }
        if (filters.status) {
            tripsQuery = tripsQuery.eq('status', filters.status);
        }
        if (filters.date) {
            const startDate = new Date(filters.date);
            startDate.setHours(0, 0, 0, 0);
            const endDate = new Date(filters.date);
            endDate.setHours(23, 59, 59, 999);
            tripsQuery = tripsQuery
                .gte('departure_time', startDate.toISOString())
                .lte('departure_time', endDate.toISOString());
        }

        const { data: tripsData } = await tripsQuery;
        if (tripsData) setDriverTrips(tripsData);

        const { data: driversData } = await supabase
            .from('profiles')
            .select('*')
            .eq('role', 'driver');

        if (driversData) setDrivers(driversData);
    };

    const handleCreateBooking = async (e: React.FormEvent) => {
        e.preventDefault();
        const { error } = await supabase.from('bookings').insert([
            {
                ...newBooking,
                status: newBooking.assigned_driver_id ? 'assigned' : 'pending',
            },
        ]);

        if (!error) {
            setShowNewBooking(false);
            setNewBooking({
                customer_name: '',
                customer_phone: '',
                pickup_location: '',
                dropoff_location: '',
                scheduled_time: '',
                price: '',
                assigned_driver_id: '',
                booking_type: 'custom_request',
            });
            fetchData();
        } else {
            alert('Error creating booking: ' + error.message);
        }
    };

    const handleUpdateTripPrice = async (tripId: string, field: 'price_per_seat' | 'whole_car_price', value: number) => {
        const { error } = await supabase
            .from('driver_trips')
            .update({ [field]: value })
            .eq('id', tripId);

        if (!error) {
            setEditingPrice(null);
            fetchData();
        } else {
            alert('Error updating price: ' + error.message);
        }
    };

    const handleMatchRequest = async (requestId: string, tripId: string, seatsToAssign?: number) => {
        const request = customRequests.find(r => r.id === requestId);
        const trip = driverTrips.find(t => t.id === tripId);

        if (!request || !trip) return;

        const availableSeats = trip.available_seats - trip.booked_seats;
        const seats = seatsToAssign || matchingSeats[`${requestId}-${tripId}`] || request.seats_booked || 1;
        
        if (seats > availableSeats) {
            alert(`Not enough seats available. Only ${availableSeats} seats available.`);
            return;
        }

        if (seats > request.seats_booked) {
            alert(`Cannot assign more seats than requested. Customer requested ${request.seats_booked} seat(s).`);
            return;
        }

        const updateData: any = {
            driver_trip_id: tripId,
            assigned_driver_id: trip.driver_id,
            status: 'assigned',
            seats_booked: seats,
            price: seats * trip.price_per_seat,
        };

        const { error: bookingError } = await supabase
            .from('bookings')
            .update(updateData)
            .eq('id', requestId);

        if (!bookingError) {
            const newBookedSeats = trip.booked_seats + seats;

            const { error: tripError } = await supabase
                .from('driver_trips')
                .update({ booked_seats: newBookedSeats })
                .eq('id', tripId);

            if (!tripError) {
                setMatchingRequest(null);
                setMatchingSeats({});
                fetchData();
            } else {
                alert('Error updating trip: ' + tripError.message);
            }
        } else {
            alert('Error matching request: ' + bookingError.message);
        }
    };

    const handleAssignDriver = async (requestId: string, driverId: string, price?: number) => {
        const updateData: any = {
            assigned_driver_id: driverId,
            status: 'assigned',
        };

        if (price) {
            updateData.price = price;
        }

        const { error } = await supabase
            .from('bookings')
            .update(updateData)
            .eq('id', requestId);

        if (!error) {
            fetchData();
        } else {
            alert('Error assigning driver: ' + error.message);
        }
    };

    const handleUpdateBookingPrice = async (bookingId: string, price: number) => {
        const { error } = await supabase
            .from('bookings')
            .update({ price })
            .eq('id', bookingId);

        if (!error) {
            fetchData();
        } else {
            alert('Error updating price: ' + error.message);
        }
    };

    return (
        <Layout>
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24 py-12">
                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 mb-10">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
                        <p className="text-lg text-gray-600">Manage trips, bookings, and drivers</p>
                    </div>
                    <button
                        onClick={() => setShowNewBooking(true)}
                        className="flex items-center gap-2 px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-all duration-200 shadow-lg hover:shadow-xl"
                    >
                        <Plus size={20} />
                        New Booking (Phone)
                    </button>
                </div>

                {/* Drivers Status */}
                <div className="mb-10">
                    <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
                        <User size={24} />
                        Active Drivers
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {drivers.map((driver) => (
                            <div
                                key={driver.id}
                                className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 flex justify-between items-center hover:shadow-xl transition-all duration-300"
                            >
                                <div>
                                    <p className="font-semibold text-gray-900">{driver.full_name}</p>
                                    <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                                        <Phone size={14} />
                                        {driver.phone_number}
                                    </p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                    driver.is_active
                                        ? 'bg-green-100 text-green-800'
                                        : 'bg-gray-100 text-gray-800'
                                }`}>
                                    {driver.is_active ? 'Online' : 'Offline'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Tabs */}
                <div className="mb-8 border-b border-gray-200">
                    <nav className="flex space-x-8">
                        <button
                            onClick={() => setActiveTab('trips')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                                activeTab === 'trips'
                                    ? 'border-ethiopian-green text-ethiopian-green'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            Driver Trips
                        </button>
                        <button
                            onClick={() => setActiveTab('custom-requests')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                                activeTab === 'custom-requests'
                                    ? 'border-ethiopian-green text-ethiopian-green'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            Custom Requests ({customRequests.length})
                        </button>
                        <button
                            onClick={() => setActiveTab('all-bookings')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                                activeTab === 'all-bookings'
                                    ? 'border-ethiopian-green text-ethiopian-green'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            All Bookings
                        </button>
                    </nav>
                </div>

                {/* Filters */}
                <div className="mb-8 bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Filter size={20} className="text-gray-400" />
                        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="relative">
                            <Calendar size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                            <input
                                type="date"
                                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                value={filters.date}
                                onChange={e => setFilters({ ...filters, date: e.target.value })}
                            />
                        </div>
                        <select
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                            value={filters.driver}
                            onChange={e => setFilters({ ...filters, driver: e.target.value })}
                        >
                            <option value="">All Drivers</option>
                            {drivers.map(d => (
                                <option key={d.id} value={d.id}>{d.full_name}</option>
                            ))}
                        </select>
                        <select
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                            value={filters.status}
                            onChange={e => setFilters({ ...filters, status: e.target.value })}
                        >
                            <option value="">All Status</option>
                            <option value="scheduled">Scheduled</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                        <button
                            onClick={() => setFilters({ date: '', driver: '', status: '' })}
                            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                        >
                            Clear Filters
                        </button>
                    </div>
                </div>

                {/* Driver Trips Tab */}
                {activeTab === 'trips' && (
                    <div className="space-y-6">
                        {driverTrips.length === 0 ? (
                            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-16 text-center">
                                <MapPin size={48} className="mx-auto text-gray-300 mb-4" />
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">No driver trips found</h3>
                                <p className="text-gray-600">No trips match your current filters.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {driverTrips.map((trip) => (
                                    <div
                                        key={trip.id}
                                        className="bg-white rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300"
                                    >
                                        <div className="p-8">
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="flex-1">
                                                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                                                        {trip.origin} → {trip.destination}
                                                    </h3>
                                                    <div className="space-y-2 text-sm text-gray-600">
                                                        <div className="flex items-center gap-2">
                                                            <Users size={16} className="text-gray-400" />
                                                            {trip.profiles?.full_name} | {trip.profiles?.phone_number}
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <Clock size={16} className="text-gray-400" />
                                                            {new Date(trip.departure_time).toLocaleString()}
                                                        </div>
                                                    </div>
                                                </div>
                                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                                    trip.status === 'scheduled' ? 'bg-green-100 text-green-800' :
                                                    trip.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                                                    'bg-yellow-100 text-yellow-800'
                                                }`}>
                                                    {trip.status}
                                                </span>
                                            </div>

                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                                                <div>
                                                    <p className="text-xs text-gray-500 mb-1">Available Seats</p>
                                                    <p className="text-lg font-bold text-gray-900">
                                                        {trip.available_seats - trip.booked_seats} / {trip.available_seats}
                                                    </p>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-500 mb-1">Price per Seat</p>
                                                    <div className="flex items-center gap-2">
                                                        {editingPrice?.tripId === trip.id && editingPrice.field === 'price_per_seat' ? (
                                                            <input
                                                                type="number"
                                                                step="0.01"
                                                                className="w-24 px-2 py-1 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green"
                                                                defaultValue={trip.price_per_seat}
                                                                onBlur={(e) => {
                                                                    if (e.target.value) {
                                                                        handleUpdateTripPrice(trip.id, 'price_per_seat', parseFloat(e.target.value));
                                                                    } else {
                                                                        setEditingPrice(null);
                                                                    }
                                                                }}
                                                                autoFocus
                                                            />
                                                        ) : (
                                                            <>
                                                                <p className="text-lg font-bold text-gray-900">{trip.price_per_seat} ETB</p>
                                                                <button
                                                                    onClick={() => setEditingPrice({ tripId: trip.id, field: 'price_per_seat' })}
                                                                    className="text-blue-600 hover:text-blue-800 transition-colors"
                                                                >
                                                                    <Edit size={16} />
                                                                </button>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-500 mb-1">Whole Car</p>
                                                    <div className="flex items-center gap-2">
                                                        {editingPrice?.tripId === trip.id && editingPrice.field === 'whole_car_price' ? (
                                                            <input
                                                                type="number"
                                                                step="0.01"
                                                                className="w-24 px-2 py-1 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green"
                                                                defaultValue={trip.whole_car_price}
                                                                onBlur={(e) => {
                                                                    if (e.target.value) {
                                                                        handleUpdateTripPrice(trip.id, 'whole_car_price', parseFloat(e.target.value));
                                                                    } else {
                                                                        setEditingPrice(null);
                                                                    }
                                                                }}
                                                                autoFocus
                                                            />
                                                        ) : (
                                                            <>
                                                                <p className="text-lg font-bold text-gray-900">{trip.whole_car_price} ETB</p>
                                                                <button
                                                                    onClick={() => setEditingPrice({ tripId: trip.id, field: 'whole_car_price' })}
                                                                    className="text-blue-600 hover:text-blue-800 transition-colors"
                                                                >
                                                                    <Edit size={16} />
                                                                </button>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-500 mb-1">Bookings</p>
                                                    <p className="text-lg font-bold text-gray-900">{trip.bookings?.length || 0}</p>
                                                </div>
                                            </div>

                                            {trip.bookings && trip.bookings.length > 0 && (
                                                <div className="mt-6 pt-6 border-t border-gray-100">
                                                    <p className="text-sm font-semibold text-gray-700 mb-3">Bookings:</p>
                                                    <div className="space-y-2">
                                                        {trip.bookings.map((booking: any) => (
                                                            <div key={booking.id} className="text-sm bg-gray-50 p-3 rounded-lg flex justify-between items-center">
                                                                <span className="text-gray-900">
                                                                    <span className="font-semibold">{booking.customer_name}</span> - {booking.booking_type === 'whole_car' ? 'Whole Car' : `${booking.seats_booked} seat(s)`} - {booking.price} ETB
                                                                </span>
                                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                                                    booking.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                                    booking.status === 'assigned' ? 'bg-blue-100 text-blue-800' :
                                                                    'bg-yellow-100 text-yellow-800'
                                                                }`}>
                                                                    {booking.status}
                                                                </span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Custom Requests Tab */}
                {activeTab === 'custom-requests' && (
                    <div className="space-y-6">
                        {customRequests.length === 0 ? (
                            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-16 text-center">
                                <CheckCircle2 size={48} className="mx-auto text-gray-300 mb-4" />
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">No pending custom requests</h3>
                                <p className="text-gray-600">All requests have been processed.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {customRequests.map((request) => (
                                    <div
                                        key={request.id}
                                        className="bg-white rounded-2xl shadow-lg border-l-4 border-yellow-500 hover:shadow-xl transition-all duration-300"
                                    >
                                        <div className="p-8">
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="flex-1">
                                                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                                                        {request.pickup_location} → {request.dropoff_location}
                                                    </h3>
                                                    <div className="space-y-2 text-sm text-gray-600">
                                                        <div className="flex items-center gap-2">
                                                            <Users size={16} className="text-gray-400" />
                                                            {request.customer_name} | {request.customer_phone}
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <Clock size={16} className="text-gray-400" />
                                                            {new Date(request.scheduled_time).toLocaleString()}
                                                        </div>
                                                        {request.notes && (
                                                            <p className="text-gray-500 italic">Notes: {request.notes}</p>
                                                        )}
                                                        <div className="flex items-center gap-2 mt-2">
                                                            <Users size={16} className="text-gray-400" />
                                                            <span className="text-sm font-semibold text-gray-700">
                                                                Seats Requested: {request.seats_booked || 1}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800">
                                                    Pending
                                                </span>
                                            </div>

                                            <div className="flex flex-wrap gap-3 mb-6">
                                                <button
                                                    onClick={() => setMatchingRequest(request.id)}
                                                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                                                >
                                                    <LinkIcon size={16} />
                                                    Match with Trip
                                                </button>
                                                <select
                                                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                                    onChange={(e) => {
                                                        if (e.target.value) {
                                                            const [driverId, price] = e.target.value.split('|');
                                                            handleAssignDriver(request.id, driverId, price ? parseFloat(price) : undefined);
                                                        }
                                                    }}
                                                >
                                                    <option value="">Assign Driver Manually</option>
                                                    {drivers.map(d => (
                                                        <option key={d.id} value={`${d.id}|${request.price || ''}`}>
                                                            {d.full_name} {request.price ? `(${request.price} ETB)` : ''}
                                                        </option>
                                                    ))}
                                                </select>
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    placeholder="Set Price"
                                                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all w-32"
                                                    onBlur={(e) => {
                                                        if (e.target.value) {
                                                            handleUpdateBookingPrice(request.id, parseFloat(e.target.value));
                                                        }
                                                    }}
                                                />
                                            </div>

                                            {/* Matching Modal */}
                                            {matchingRequest === request.id && (
                                                <div className="mt-6 p-6 bg-gray-50 rounded-lg border border-gray-200">
                                                    <div className="flex justify-between items-center mb-4">
                                                        <h4 className="font-semibold text-gray-900">Match with Available Trip</h4>
                                                        <button
                                                            onClick={() => setMatchingRequest(null)}
                                                            className="text-gray-400 hover:text-gray-600"
                                                        >
                                                            <X size={20} />
                                                        </button>
                                                    </div>
                                                    <div className="space-y-3 max-h-60 overflow-y-auto">
                                                        {driverTrips
                                                            .filter(t => t.status === 'scheduled' && new Date(t.departure_time) >= new Date(request.scheduled_time))
                                                            .map(trip => {
                                                                const availableSeats = trip.available_seats - trip.booked_seats;
                                                                const requestedSeats = request.seats_booked || 1;
                                                                const maxSeats = Math.min(availableSeats, requestedSeats);
                                                                const canMatch = availableSeats > 0 && requestedSeats > 0;
                                                                const seatKey = `${request.id}-${trip.id}`;
                                                                const selectedSeats = matchingSeats[seatKey] || Math.min(requestedSeats, availableSeats);
                                                                const calculatedPrice = selectedSeats * trip.price_per_seat;
                                                                
                                                                return (
                                                                    <div key={trip.id} className={`p-4 border rounded-lg ${
                                                                        canMatch ? 'border-green-300 bg-green-50' : 'border-gray-300 bg-gray-50'
                                                                    }`}>
                                                                        <div className="space-y-3">
                                                                            <div className="flex justify-between items-start">
                                                                                <div>
                                                                                    <p className="font-semibold text-gray-900">{trip.origin} → {trip.destination}</p>
                                                                                    <p className="text-xs text-gray-500 mt-1">
                                                                                        {new Date(trip.departure_time).toLocaleString()} | {availableSeats} seats available
                                                                                    </p>
                                                                                    <p className="text-xs text-gray-600 mt-1">
                                                                                        Price per seat: {trip.price_per_seat} ETB
                                                                                    </p>
                                                                                </div>
                                                                            </div>
                                                                            {canMatch ? (
                                                                                <div className="flex gap-3 items-end">
                                                                                    <div className="flex-1">
                                                                                        <label className="block text-xs font-medium text-gray-700 mb-1">
                                                                                            Seats to Assign (max {maxSeats})
                                                                                        </label>
                                                                                        <input
                                                                                            type="number"
                                                                                            min="1"
                                                                                            max={maxSeats}
                                                                                            value={selectedSeats}
                                                                                            onChange={(e) => {
                                                                                                const seats = parseInt(e.target.value) || 1;
                                                                                                setMatchingSeats({
                                                                                                    ...matchingSeats,
                                                                                                    [seatKey]: Math.min(Math.max(1, seats), maxSeats)
                                                                                                });
                                                                                            }}
                                                                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                                                                        />
                                                                                        <p className="text-xs text-gray-600 mt-1">
                                                                                            Total: {calculatedPrice} ETB
                                                                                        </p>
                                                                                    </div>
                                                                                    <button
                                                                                        onClick={() => handleMatchRequest(request.id, trip.id, selectedSeats)}
                                                                                        className="px-4 py-2 bg-ethiopian-green text-white rounded-lg text-sm font-semibold hover:bg-ethiopian-green/90 transition-colors whitespace-nowrap"
                                                                                    >
                                                                                        Match
                                                                                    </button>
                                                                                </div>
                                                                            ) : (
                                                                                <span className="text-xs text-gray-500">Not enough seats available</span>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                );
                                                            })}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* All Bookings Tab */}
                {activeTab === 'all-bookings' && (
                    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
                        <div className="divide-y divide-gray-100">
                            {bookings.map((booking) => (
                                <div key={booking.id} className="p-6 hover:bg-gray-50 transition-colors">
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <p className="text-lg font-semibold text-gray-900 mb-1">
                                                {booking.pickup_location} → {booking.dropoff_location}
                                            </p>
                                            <div className="space-y-1 text-sm text-gray-600">
                                                <p>{booking.customer_name} | {new Date(booking.scheduled_time).toLocaleString()}</p>
                                                <p className="text-xs text-gray-500">
                                                    Type: {booking.booking_type} | {booking.driver_trips ? 'Trip Booking' : 'Custom Request'}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end gap-3">
                                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                                booking.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                booking.status === 'assigned' ? 'bg-blue-100 text-blue-800' :
                                                'bg-yellow-100 text-yellow-800'
                                            }`}>
                                                {booking.status}
                                            </span>
                                            <div className="flex items-center gap-2">
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    className="w-28 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all text-sm"
                                                    defaultValue={booking.price}
                                                    onBlur={(e) => {
                                                        if (e.target.value) {
                                                            handleUpdateBookingPrice(booking.id, parseFloat(e.target.value));
                                                        }
                                                    }}
                                                />
                                                <span className="text-sm text-gray-500">ETB</span>
                                            </div>
                                            <p className="text-sm text-gray-600">
                                                {booking.profiles?.full_name || booking.driver_trips?.profiles?.full_name || 'Unassigned'}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* New Booking Modal */}
                {showNewBooking && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                            <div className="p-8">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-2xl font-bold text-gray-900">Create New Booking (Phone Call)</h3>
                                    <button
                                        onClick={() => setShowNewBooking(false)}
                                        className="text-gray-400 hover:text-gray-600 transition-colors"
                                    >
                                        <X size={24} />
                                    </button>
                                </div>
                                <form onSubmit={handleCreateBooking} className="space-y-5">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Customer Name</label>
                                        <input
                                            placeholder="Enter customer name"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newBooking.customer_name}
                                            onChange={e => setNewBooking({ ...newBooking, customer_name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Customer Phone</label>
                                        <input
                                            placeholder="Enter phone number"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newBooking.customer_phone}
                                            onChange={e => setNewBooking({ ...newBooking, customer_phone: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Pickup Location</label>
                                        <select
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all bg-white"
                                            value={newBooking.pickup_location}
                                            onChange={e => setNewBooking({ ...newBooking, pickup_location: e.target.value })}
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
                                            value={newBooking.dropoff_location}
                                            onChange={e => setNewBooking({ ...newBooking, dropoff_location: e.target.value })}
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
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Scheduled Date & Time</label>
                                        <input
                                            type="datetime-local"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newBooking.scheduled_time}
                                            onChange={e => setNewBooking({ ...newBooking, scheduled_time: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Price (ETB)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            placeholder="Enter price"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newBooking.price}
                                            onChange={e => setNewBooking({ ...newBooking, price: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Assign Driver (Optional)</label>
                                        <select
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newBooking.assigned_driver_id}
                                            onChange={e => setNewBooking({ ...newBooking, assigned_driver_id: e.target.value })}
                                        >
                                            <option value="">Select a driver</option>
                                            {drivers.map(d => (
                                                <option key={d.id} value={d.id}>{d.full_name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="flex justify-end gap-3 pt-4">
                                        <button
                                            type="button"
                                            onClick={() => setShowNewBooking(false)}
                                            className="px-6 py-3 text-gray-700 bg-gray-100 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            className="px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors shadow-lg hover:shadow-xl"
                                        >
                                            Create Booking
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
