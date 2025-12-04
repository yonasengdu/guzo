import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { Power, MapPin, Phone, Clock, Plus, Edit, Trash2, Users, X, CheckCircle2, Navigation } from 'lucide-react';
import { LOCATIONS } from '../constants/locations';

export default function DriverDashboard() {
    const { user, profile } = useAuth();
    const [isActive, setIsActive] = useState(false);
    const [assignedBookings, setAssignedBookings] = useState<any[]>([]);
    const [myTrips, setMyTrips] = useState<any[]>([]);
    const [pendingRequests, setPendingRequests] = useState<any[]>([]);
    const [showCreateTrip, setShowCreateTrip] = useState(false);
    const [editingTrip, setEditingTrip] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'trips' | 'bookings' | 'requests'>('trips');
    const [assigningRequest, setAssigningRequest] = useState<string | null>(null);
    const [assignmentSeats, setAssignmentSeats] = useState<{ [key: string]: number }>({});

    const [newTrip, setNewTrip] = useState({
        origin: '',
        destination: '',
        departure_time: '',
        available_seats: '',
        price_per_seat: '',
        whole_car_price: '',
    });

    useEffect(() => {
        if (profile) {
            setIsActive(profile.is_active);
            fetchBookings();
            fetchMyTrips();
            fetchPendingRequests();
        }
    }, [profile]);

    const fetchBookings = async () => {
        if (!user) return;

        const { data } = await supabase
            .from('bookings')
            .select('*')
            .eq('assigned_driver_id', user.id)
            .neq('status', 'completed')
            .order('scheduled_time', { ascending: true });

        if (data) setAssignedBookings(data);
    };

    const fetchMyTrips = async () => {
        if (!user) return;

        const { data } = await supabase
            .from('driver_trips')
            .select('*, bookings(*)')
            .eq('driver_id', user.id)
            .order('departure_time', { ascending: true });

        if (data) setMyTrips(data);
    };

    const fetchPendingRequests = async () => {
        if (!user) return;

        const { data } = await supabase
            .from('bookings')
            .select('*')
            .eq('booking_type', 'custom_request')
            .eq('status', 'pending')
            .is('driver_trip_id', null) // Not yet assigned to any trip
            .order('created_at', { ascending: false });

        if (data) setPendingRequests(data);
    };

    const toggleStatus = async () => {
        if (!user) return;

        const newStatus = !isActive;
        setIsActive(newStatus);

        const { error } = await supabase
            .from('profiles')
            .update({ is_active: newStatus })
            .eq('id', user.id);

        if (error) {
            console.error('Error updating status:', error);
            setIsActive(!newStatus);
        }
    };

    const handleCreateTrip = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;

        const { error } = await supabase.from('driver_trips').insert([
            {
                driver_id: user.id,
                origin: newTrip.origin,
                destination: newTrip.destination,
                departure_time: newTrip.departure_time,
                available_seats: parseInt(newTrip.available_seats),
                price_per_seat: parseFloat(newTrip.price_per_seat),
                whole_car_price: parseFloat(newTrip.whole_car_price),
            },
        ]);

        if (!error) {
            setShowCreateTrip(false);
            setNewTrip({
                origin: '',
                destination: '',
                departure_time: '',
                available_seats: '',
                price_per_seat: '',
                whole_car_price: '',
            });
            fetchMyTrips();
        } else {
            alert('Error creating trip: ' + error.message);
        }
    };

    const handleUpdateTrip = async (tripId: string, updates: any) => {
        const { error } = await supabase
            .from('driver_trips')
            .update(updates)
            .eq('id', tripId);

        if (!error) {
            setEditingTrip(null);
            fetchMyTrips();
        } else {
            alert('Error updating trip: ' + error.message);
        }
    };

    const handleDeleteTrip = async (tripId: string) => {
        if (!confirm('Are you sure you want to delete this trip?')) return;

        const { error } = await supabase
            .from('driver_trips')
            .delete()
            .eq('id', tripId);

        if (!error) {
            fetchMyTrips();
        } else {
            alert('Error deleting trip: ' + error.message);
        }
    };

    const completeJob = async (bookingId: string) => {
        const { error } = await supabase
            .from('bookings')
            .update({ status: 'completed' })
            .eq('id', bookingId);

        if (!error) {
            fetchBookings();
        }
    };

    const getTripBookings = (tripId: string) => {
        const trip = myTrips.find(t => t.id === tripId);
        return trip?.bookings || [];
    };

    const handleAssignRequest = async (requestId: string, tripId: string, seats: number) => {
        if (!user) return;

        const request = pendingRequests.find(r => r.id === requestId);
        const trip = myTrips.find(t => t.id === tripId);

        if (!request || !trip) return;

        const availableSeats = trip.available_seats - trip.booked_seats;
        if (seats > availableSeats) {
            alert(`Not enough seats available. Only ${availableSeats} seats available.`);
            return;
        }

        if (seats > request.seats_booked) {
            alert(`Cannot assign more seats than requested. Customer requested ${request.seats_booked} seat(s).`);
            return;
        }

        const price = seats * trip.price_per_seat;

        // Update booking
        const { error: bookingError } = await supabase
            .from('bookings')
            .update({
                driver_trip_id: tripId,
                assigned_driver_id: user.id,
                status: 'assigned',
                seats_booked: seats,
                price: price,
            })
            .eq('id', requestId);

        if (!bookingError) {
            // Update trip booked_seats
            const { error: tripError } = await supabase
                .from('driver_trips')
                .update({ booked_seats: trip.booked_seats + seats })
                .eq('id', tripId);

            if (!tripError) {
                setAssigningRequest(null);
                setAssignmentSeats({});
                fetchPendingRequests();
                fetchMyTrips();
                fetchBookings();
            } else {
                alert('Error updating trip: ' + tripError.message);
            }
        } else {
            alert('Error assigning request: ' + bookingError.message);
        }
    };

    return (
        <Layout>
            <div className="max-w-[1600px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24 py-12">
                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 mb-10">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-900 mb-2">Driver Dashboard</h1>
                        <p className="text-lg text-gray-600">Welcome back, {profile?.full_name}</p>
                    </div>
                    <button
                        onClick={toggleStatus}
                        className={`flex items-center gap-2 px-8 py-4 rounded-full font-bold text-white transition-all duration-200 shadow-lg hover:shadow-xl ${
                            isActive
                                ? 'bg-green-600 hover:bg-green-700'
                                : 'bg-red-600 hover:bg-red-700'
                        }`}
                    >
                        <Power size={20} />
                        {isActive ? 'ONLINE' : 'OFFLINE'}
                    </button>
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
                            My Trips
                        </button>
                        <button
                            onClick={() => setActiveTab('requests')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                                activeTab === 'requests'
                                    ? 'border-ethiopian-green text-ethiopian-green'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            Pending Requests ({pendingRequests.length})
                        </button>
                        <button
                            onClick={() => setActiveTab('bookings')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                                activeTab === 'bookings'
                                    ? 'border-ethiopian-green text-ethiopian-green'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            Assigned Jobs ({assignedBookings.length})
                        </button>
                    </nav>
                </div>

                {/* My Trips Tab */}
                {activeTab === 'trips' && (
                    <div className="space-y-8">
                        <div className="flex justify-between items-center">
                            <h2 className="text-2xl font-semibold text-gray-900">My Trips</h2>
                            <button
                                onClick={() => setShowCreateTrip(true)}
                                className="flex items-center gap-2 px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-all duration-200 shadow-lg hover:shadow-xl"
                            >
                                <Plus size={20} />
                                Create Trip
                            </button>
                        </div>

                        {myTrips.length === 0 ? (
                            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-16 text-center">
                                <MapPin size={48} className="mx-auto text-gray-300 mb-4" />
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">No trips created yet</h3>
                                <p className="text-gray-600 mb-6">Create your first trip to start accepting bookings!</p>
                                <button
                                    onClick={() => setShowCreateTrip(true)}
                                    className="px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors"
                                >
                                    Create Trip
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {myTrips.map((trip) => (
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
                                                    <div className="flex items-center gap-2 text-sm text-gray-600">
                                                        <Clock size={16} className="text-gray-400" />
                                                        {new Date(trip.departure_time).toLocaleString()}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                                        trip.status === 'scheduled' ? 'bg-green-100 text-green-800' :
                                                        trip.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                                                        'bg-yellow-100 text-yellow-800'
                                                    }`}>
                                                        {trip.status}
                                                    </span>
                                                    {trip.status === 'scheduled' && (
                                                        <>
                                                            <button
                                                                onClick={() => setEditingTrip(trip.id)}
                                                                className="text-blue-600 hover:text-blue-800 transition-colors"
                                                            >
                                                                <Edit size={20} />
                                                            </button>
                                                            <button
                                                                onClick={() => handleDeleteTrip(trip.id)}
                                                                className="text-red-600 hover:text-red-800 transition-colors"
                                                            >
                                                                <Trash2 size={20} />
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                                                <div>
                                                    <p className="text-xs text-gray-500 mb-1">Available Seats</p>
                                                    <p className="text-lg font-bold text-gray-900 flex items-center gap-1">
                                                        <Users size={16} />
                                                        {trip.available_seats - trip.booked_seats} / {trip.available_seats}
                                                    </p>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-500 mb-1">Price per Seat</p>
                                                    <p className="text-lg font-bold text-gray-900">{trip.price_per_seat} ETB</p>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-500 mb-1">Whole Car</p>
                                                    <p className="text-lg font-bold text-gray-900">{trip.whole_car_price} ETB</p>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-500 mb-1">Bookings</p>
                                                    <p className="text-lg font-bold text-gray-900">{getTripBookings(trip.id).length}</p>
                                                </div>
                                            </div>

                                            {editingTrip === trip.id && (
                                                <div className="mt-6 p-6 bg-gray-50 rounded-lg border border-gray-200">
                                                    <h4 className="font-semibold text-gray-900 mb-4">Edit Trip Pricing</h4>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 mb-2">Price per Seat</label>
                                                            <input
                                                                type="number"
                                                                step="0.01"
                                                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                                                defaultValue={trip.price_per_seat}
                                                                onBlur={(e) => {
                                                                    if (e.target.value) {
                                                                        handleUpdateTrip(trip.id, { price_per_seat: parseFloat(e.target.value) });
                                                                    }
                                                                }}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 mb-2">Whole Car Price</label>
                                                            <input
                                                                type="number"
                                                                step="0.01"
                                                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                                                defaultValue={trip.whole_car_price}
                                                                onBlur={(e) => {
                                                                    if (e.target.value) {
                                                                        handleUpdateTrip(trip.id, { whole_car_price: parseFloat(e.target.value) });
                                                                    }
                                                                }}
                                                            />
                                                        </div>
                                                    </div>
                                                    <button
                                                        onClick={() => setEditingTrip(null)}
                                                        className="mt-4 text-sm text-gray-600 hover:text-gray-800 font-medium"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            )}

                                            {getTripBookings(trip.id).length > 0 && (
                                                <div className="mt-6 pt-6 border-t border-gray-100">
                                                    <p className="text-sm font-semibold text-gray-700 mb-3">Bookings for this trip:</p>
                                                    <div className="space-y-2">
                                                        {getTripBookings(trip.id).map((booking: any) => (
                                                            <div key={booking.id} className="text-sm bg-gray-50 p-3 rounded-lg">
                                                                <span className="font-semibold text-gray-900">{booking.customer_name}</span>
                                                                <span className="text-gray-600"> - {booking.booking_type === 'whole_car' ? 'Whole Car' : `${booking.seats_booked} seat(s)`}</span>
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

                {/* Pending Requests Tab */}
                {activeTab === 'requests' && (
                    <div className="space-y-6">
                        <h2 className="text-2xl font-semibold text-gray-900">Pending Booking Requests</h2>

                        {pendingRequests.length === 0 ? (
                            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-16 text-center">
                                <CheckCircle2 size={48} className="mx-auto text-gray-300 mb-4" />
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">No pending requests</h3>
                                <p className="text-gray-600">All booking requests have been assigned.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {pendingRequests.map((request) => {
                                    // Find matching trips for this request (same origin/destination, not full)
                                    const matchingTrips = myTrips.filter(trip => 
                                        trip.status === 'scheduled' &&
                                        trip.origin === request.pickup_location &&
                                        trip.destination === request.dropoff_location &&
                                        (trip.available_seats - trip.booked_seats) > 0 &&
                                        new Date(trip.departure_time) >= new Date(request.scheduled_time)
                                    );

                                    return (
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
                                                            <div className="flex items-center gap-2">
                                                                <Users size={16} className="text-gray-400" />
                                                                Seats Requested: {request.seats_booked || 1}
                                                            </div>
                                                            {request.notes && (
                                                                <p className="text-gray-500 italic">Notes: {request.notes}</p>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800">
                                                        Pending
                                                    </span>
                                                </div>

                                                {matchingTrips.length > 0 ? (
                                                    <div className="space-y-3">
                                                        <p className="text-sm font-semibold text-gray-700 mb-3">
                                                            Available Trips on This Route:
                                                        </p>
                                                        {matchingTrips.map((trip) => {
                                                            const availableSeats = trip.available_seats - trip.booked_seats;
                                                            const maxSeats = Math.min(availableSeats, request.seats_booked || 1);
                                                            const seatKey = `${request.id}-${trip.id}`;
                                                            const selectedSeats = assignmentSeats[seatKey] || Math.min(maxSeats, request.seats_booked || 1);
                                                            const calculatedPrice = selectedSeats * trip.price_per_seat;

                                                            return (
                                                                <div key={trip.id} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                                                                    <div className="space-y-3">
                                                                        <div>
                                                                            <p className="font-semibold text-gray-900">{trip.origin} → {trip.destination}</p>
                                                                            <p className="text-xs text-gray-500 mt-1">
                                                                                {new Date(trip.departure_time).toLocaleString()} | {availableSeats} seats available
                                                                            </p>
                                                                            <p className="text-xs text-gray-600 mt-1">
                                                                                Price per seat: {trip.price_per_seat} ETB
                                                                            </p>
                                                                        </div>
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
                                                                                        setAssignmentSeats({
                                                                                            ...assignmentSeats,
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
                                                                                onClick={() => handleAssignRequest(request.id, trip.id, selectedSeats)}
                                                                                className="px-4 py-2 bg-ethiopian-green text-white rounded-lg text-sm font-semibold hover:bg-ethiopian-green/90 transition-colors whitespace-nowrap"
                                                                            >
                                                                                Assign
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                ) : (
                                                    <div className="text-center py-4 text-gray-500">
                                                        <p className="text-sm">No matching trips available for this route.</p>
                                                        <p className="text-xs mt-1">Create a trip with this route to assign this request.</p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {/* Assigned Jobs Tab */}
                {activeTab === 'bookings' && (
                    <div className="space-y-6">
                        <h2 className="text-2xl font-semibold text-gray-900">Assigned Jobs (Custom Requests)</h2>

                        {assignedBookings.length === 0 ? (
                            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-16 text-center">
                                <CheckCircle2 size={48} className="mx-auto text-gray-300 mb-4" />
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">No active jobs assigned</h3>
                                <p className="text-gray-600">Stay online to receive custom trip requests!</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {assignedBookings.map((booking) => (
                                    <div
                                        key={booking.id}
                                        className="bg-white rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300"
                                    >
                                        <div className="p-8">
                                            <div className="flex justify-between items-start mb-6">
                                                <div>
                                                    <h3 className="text-xl font-bold text-gray-900 mb-2">{booking.customer_name}</h3>
                                                    <a
                                                        href={`tel:${booking.customer_phone}`}
                                                        className="flex items-center gap-2 text-ethiopian-green hover:text-ethiopian-green/80 transition-colors font-medium"
                                                    >
                                                        <Phone size={18} />
                                                        {booking.customer_phone}
                                                    </a>
                                                </div>
                                                <div className="text-right">
                                                    <div className="flex items-center gap-2 justify-end text-gray-900 font-semibold mb-1">
                                                        <Clock size={18} />
                                                        {new Date(booking.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </div>
                                                    <p className="text-sm text-gray-500">
                                                        {new Date(booking.scheduled_time).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="space-y-4 mb-6">
                                                <div className="flex items-start gap-4">
                                                    <div className="mt-1">
                                                        <div className="w-3 h-3 rounded-full bg-green-600" />
                                                    </div>
                                                    <div className="flex-1">
                                                        <p className="text-xs text-gray-500 uppercase mb-1">Pickup</p>
                                                        <p className="text-gray-900 font-medium">{booking.pickup_location}</p>
                                                    </div>
                                                </div>
                                                <div className="flex items-start gap-4">
                                                    <div className="mt-1">
                                                        <MapPin size={18} className="text-red-600" />
                                                    </div>
                                                    <div className="flex-1">
                                                        <p className="text-xs text-gray-500 uppercase mb-1">Dropoff</p>
                                                        <p className="text-gray-900 font-medium">{booking.dropoff_location}</p>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex gap-3 pt-6 border-t border-gray-100">
                                                <a
                                                    href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(booking.pickup_location)}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                                                >
                                                    <Navigation size={18} />
                                                    Navigate
                                                </a>
                                                <button
                                                    onClick={() => completeJob(booking.id)}
                                                    className="flex-1 px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors shadow-md hover:shadow-lg"
                                                >
                                                    Complete Job
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Create Trip Modal */}
                {showCreateTrip && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                            <div className="p-8">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-2xl font-bold text-gray-900">Create New Trip</h3>
                                    <button
                                        onClick={() => setShowCreateTrip(false)}
                                        className="text-gray-400 hover:text-gray-600 transition-colors"
                                    >
                                        <X size={24} />
                                    </button>
                                </div>
                                <form onSubmit={handleCreateTrip} className="space-y-5">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Origin</label>
                                        <select
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all bg-white"
                                            value={newTrip.origin}
                                            onChange={e => setNewTrip({ ...newTrip, origin: e.target.value })}
                                            required
                                        >
                                            <option value="">Select origin</option>
                                            {LOCATIONS.map((location) => (
                                                <option key={location} value={location}>
                                                    {location}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Destination</label>
                                        <select
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all bg-white"
                                            value={newTrip.destination}
                                            onChange={e => setNewTrip({ ...newTrip, destination: e.target.value })}
                                            required
                                        >
                                            <option value="">Select destination</option>
                                            {LOCATIONS.map((location) => (
                                                <option key={location} value={location}>
                                                    {location}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Departure Date & Time</label>
                                        <input
                                            type="datetime-local"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newTrip.departure_time}
                                            onChange={e => setNewTrip({ ...newTrip, departure_time: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Available Seats</label>
                                        <input
                                            type="number"
                                            placeholder="Number of seats"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newTrip.available_seats}
                                            onChange={e => setNewTrip({ ...newTrip, available_seats: e.target.value })}
                                            min="1"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Price per Seat (ETB)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            placeholder="Enter price per seat"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newTrip.price_per_seat}
                                            onChange={e => setNewTrip({ ...newTrip, price_per_seat: e.target.value })}
                                            min="0"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Whole Car Price (ETB)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            placeholder="Enter whole car price"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-ethiopian-green transition-all"
                                            value={newTrip.whole_car_price}
                                            onChange={e => setNewTrip({ ...newTrip, whole_car_price: e.target.value })}
                                            min="0"
                                            required
                                        />
                                    </div>
                                    <div className="flex justify-end gap-3 pt-4">
                                        <button
                                            type="button"
                                            onClick={() => setShowCreateTrip(false)}
                                            className="px-6 py-3 text-gray-700 bg-gray-100 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            className="px-6 py-3 bg-ethiopian-green text-white rounded-lg font-semibold hover:bg-ethiopian-green/90 transition-colors shadow-lg hover:shadow-xl"
                                        >
                                            Create Trip
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
