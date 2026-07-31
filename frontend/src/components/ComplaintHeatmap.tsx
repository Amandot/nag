import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getHeatmapData, HeatmapLocation } from '../api/admin';
import './ComplaintHeatmap.css';

// Fix for default marker icons in Leaflet with React
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface ComplaintHeatmapProps {
  height?: string;
}

// Component to update map center when data changes
const MapCenterUpdater: React.FC<{ center: [number, number] }> = ({ center }) => {
  const map = useMap();
  
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  
  return null;
};

const ComplaintHeatmap: React.FC<ComplaintHeatmapProps> = ({ height = '500px' }) => {
  const [heatmapData, setHeatmapData] = useState<HeatmapLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    days: 30,
    priority: '',
    category: '',
    status: ''
  });

  // Default center (New Delhi coordinates)
  const defaultCenter: [number, number] = [28.6139, 77.2090];
  const [mapCenter, setMapCenter] = useState<[number, number]>(defaultCenter);

  useEffect(() => {
    fetchHeatmapData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const fetchHeatmapData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = { days: filters.days };
      if (filters.priority) params.priority = filters.priority;
      if (filters.category) params.category = filters.category;
      if (filters.status) params.status = filters.status;

      const response = await getHeatmapData(params);
      setHeatmapData(response.heatmap_data);

      // Center map on first location if available
      if (response.heatmap_data.length > 0) {
        const firstLocation = response.heatmap_data[0].location;
        setMapCenter([firstLocation.latitude, firstLocation.longitude]);
      }
    } catch (err: any) {
      console.error('Error fetching heatmap data:', err);
      setError(err.response?.data?.error || 'Failed to load heatmap data');
    } finally {
      setLoading(false);
    }
  };

  const getMarkerColor = (location: HeatmapLocation): string => {
    const { priority_distribution } = location;
    
    // Color based on highest priority complaints
    if (priority_distribution.CRITICAL > 0) {
      return '#d32f2f'; // Red for critical
    } else if (priority_distribution.HIGH > 0) {
      return '#f57c00'; // Orange for high
    } else if (priority_distribution.MEDIUM > 0) {
      return '#fbc02d'; // Yellow for medium
    } else {
      return '#388e3c'; // Green for low
    }
  };

  const createCustomIcon = (color: string) => {
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        background-color: ${color};
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      "></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });
  };

  if (loading) {
    return (
      <div className="heatmap-loading">
        <p>Loading heatmap data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="heatmap-error">
        <p>Error: {error}</p>
        <button onClick={fetchHeatmapData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="complaint-heatmap">
      {/* Filters */}
      <div className="heatmap-filters">
        <div className="filter-group">
          <label>Time Period:</label>
          <select
            value={filters.days}
            onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Priority:</label>
          <select
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
          >
            <option value="">All</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Category:</label>
          <select
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          >
            <option value="">All</option>
            <option value="Water Supply">Water Supply</option>
            <option value="Electricity">Electricity</option>
            <option value="Roads & Infrastructure">Roads & Infrastructure</option>
            <option value="Healthcare">Healthcare</option>
            <option value="Public Safety">Public Safety</option>
            <option value="Sanitation">Sanitation</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Status:</label>
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">All</option>
            <option value="Submitted">Submitted</option>
            <option value="Assigned">Assigned</option>
            <option value="In Progress">In Progress</option>
            <option value="Escalated">Escalated</option>
          </select>
        </div>
      </div>

      {/* Legend */}
      <div className="heatmap-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#d32f2f' }}></span>
          <span>Critical</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#f57c00' }}></span>
          <span>High</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#fbc02d' }}></span>
          <span>Medium</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#388e3c' }}></span>
          <span>Low</span>
        </div>
      </div>

      {/* Map */}
      <div className="heatmap-container" style={{ height }}>
        <MapContainer
          center={mapCenter}
          zoom={12}
          style={{ width: '100%', height: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          <MapCenterUpdater center={mapCenter} />

          {heatmapData.map((location, index) => (
            <Marker
              key={index}
              position={[location.location.latitude, location.location.longitude]}
              icon={createCustomIcon(getMarkerColor(location))}
            >
              <Popup>
                <div className="info-window">
                  <h3>{location.location.address}</h3>
                  <p><strong>Total Complaints:</strong> {location.complaint_count}</p>
                  <p><strong>Avg Impact Score:</strong> {location.avg_impact_score}</p>
                  <div className="priority-breakdown">
                    <p><strong>Priority Breakdown:</strong></p>
                    <ul>
                      <li>Critical: {location.priority_distribution.CRITICAL}</li>
                      <li>High: {location.priority_distribution.HIGH}</li>
                      <li>Medium: {location.priority_distribution.MEDIUM}</li>
                      <li>Low: {location.priority_distribution.LOW}</li>
                    </ul>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {heatmapData.length === 0 && (
        <div className="no-data-message">
          <p>No complaint locations available for the selected filters.</p>
          <p className="no-data-hint">Only complaints submitted with a location (map or &quot;Use Current Location&quot;) appear on the map. Try broadening filters or ask citizens to submit with location.</p>
        </div>
      )}
    </div>
  );
};

export default ComplaintHeatmap;
