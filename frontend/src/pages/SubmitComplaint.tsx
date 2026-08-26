import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { complaintsAPI, COMPLAINT_CATEGORIES } from '../api/complaints';
import Navigation from '../components/Navigation';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './SubmitComplaint.css';

// Fix for default marker icon in Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const SubmitComplaint: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    description: '',
    category: COMPLAINT_CATEGORIES[0], // Water Supply
    address: '',
    latitude: 28.6139, // Default to New Delhi
    longitude: 77.2090,
  });
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [files, setFiles] = useState<FileList | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const [markerPosition, setMarkerPosition] = useState<[number, number]>([28.6139, 77.2090]);

  // Component to handle map clicks
  const LocationMarker = () => {
    useMapEvents({
      click: async (e) => {
        const { lat, lng } = e.latlng;
        setMarkerPosition([lat, lng]);
        setFormData(prev => ({
          ...prev,
          latitude: lat,
          longitude: lng,
        }));
        
        // Reverse geocode to get address
        await reverseGeocode(lat, lng);
      },
    });

    return <Marker position={markerPosition} />;
  };

  const reverseGeocode = async (lat: number, lng: number) => {
    setLocationLoading(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
      );
      const data = await response.json();
      
      if (data.display_name) {
        setFormData(prev => ({
          ...prev,
          address: data.display_name,
        }));
      }
    } catch (err) {
      console.error('Reverse geocoding failed:', err);
      setFormData(prev => ({
        ...prev,
        address: `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`,
      }));
    } finally {
      setLocationLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(e.target.files);
  };

  const getCurrentLocation = () => {
    setLocationLoading(true);
    setError('');

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setLocationLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        
        setMarkerPosition([latitude, longitude]);
        setFormData(prev => ({
          ...prev,
          latitude,
          longitude,
        }));
        
        // Reverse geocode to get address
        await reverseGeocode(latitude, longitude);
        
        // Show map with current location
        setShowMap(true);
      },
      (error) => {
        setError('Unable to retrieve your location. Please select location on map.');
        setLocationLoading(false);
      }
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.description.trim()) {
      setError('Please provide a description of your complaint');
      return;
    }

    if (!formData.category) {
      setError('Please select a complaint type');
      return;
    }

    if (!formData.address) {
      setError('Please provide a location for your complaint');
      return;
    }

    setLoading(true);

    try {
      let submissionData: any;
      
      if (files && files.length > 0) {
        const formDataPayload = new FormData();
        formDataPayload.append('description', formData.description);
        formDataPayload.append('category', formData.category);
        formDataPayload.append('latitude', formData.latitude.toString());
        formDataPayload.append('longitude', formData.longitude.toString());
        formDataPayload.append('address', formData.address);
        
        for (let i = 0; i < files.length; i++) {
          formDataPayload.append('files', files[i]);
        }
        submissionData = formDataPayload;
      } else {
        submissionData = {
          description: formData.description,
          category: formData.category,
          location: {
            latitude: formData.latitude,
            longitude: formData.longitude,
            address: formData.address,
          }
        };
      }
      
      const complaint = await complaintsAPI.submit(submissionData);

      setSuccess(`Complaint submitted successfully! ID: ${complaint.complaint_id}`);
      
      // Navigate to complaint details after 2 seconds
      setTimeout(() => {
        navigate(`/complaint/${complaint.complaint_id}`);
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to submit complaint. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Navigation />
      <div className="container">
        <div className="submit-complaint-page">
          <h1>Submit a Complaint</h1>
          <p className="page-subtitle">Describe your issue and we'll prioritize it for resolution</p>

          <div className="card">
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="category">Type of Complaint *</label>
                <select
                  id="category"
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  disabled={loading}
                  required
                >
                  {COMPLAINT_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <small>Select the category that best matches your issue</small>
              </div>

              <div className="form-group">
                <label htmlFor="description">Complaint Description *</label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Describe your complaint in detail..."
                  rows={6}
                  disabled={loading}
                  required
                />
                <small>Be specific about the issue, location details, and any safety concerns</small>
              </div>

              <div className="form-group">
                <label>Location *</label>
                <div className="location-group">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={getCurrentLocation}
                    disabled={loading || locationLoading}
                  >
                    {locationLoading ? 'Getting Location...' : '📍 Use Current Location'}
                  </button>
                  <span className="location-or">OR</span>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowMap(!showMap)}
                    disabled={loading}
                  >
                    {showMap ? '🗺️ Hide Map' : '🗺️ Select on Map'}
                  </button>
                </div>
                
                {showMap && (
                  <div className="map-container" style={{ height: '400px', marginTop: '15px', borderRadius: '8px', overflow: 'hidden' }}>
                    <MapContainer
                      center={markerPosition}
                      zoom={13}
                      style={{ height: '100%', width: '100%' }}
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      <LocationMarker />
                    </MapContainer>
                    <small style={{ display: 'block', marginTop: '8px', color: '#666' }}>
                      Click on the map to select a location
                    </small>
                  </div>
                )}

                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  placeholder="Address will be auto-filled when you select location"
                  disabled={loading || locationLoading}
                  style={{ marginTop: '10px' }}
                />
                
                {formData.latitude !== 0 && formData.longitude !== 0 && (
                  <small className="location-info">
                    Coordinates: {formData.latitude.toFixed(6)}, {formData.longitude.toFixed(6)}
                  </small>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="files">Attachments (Optional)</label>
                <input
                  type="file"
                  id="files"
                  onChange={handleFileChange}
                  multiple
                  accept="image/*,video/*"
                  disabled={loading}
                />
                <small>Upload images or videos to support your complaint</small>
              </div>

              {error && <div className="error">{error}</div>}
              {success && <div className="success">{success}</div>}

              <div className="form-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => navigate('/dashboard')}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Submitting...' : 'Submit Complaint'}
                </button>
              </div>
            </form>
          </div>

          <div className="info-card">
            <h3>What happens next?</h3>
            <ol>
              <li>Your complaint will be analyzed using AI to determine priority</li>
              <li>It will be automatically routed to the appropriate department</li>
              <li>An officer will be assigned based on location and workload</li>
              <li>You'll receive notifications about status updates</li>
              <li>Track your complaint progress in real-time</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubmitComplaint;
