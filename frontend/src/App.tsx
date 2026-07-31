import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import RoleSelection from './pages/RoleSelection';
import Register from './pages/Register';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import SubmitComplaint from './pages/SubmitComplaint';
import ComplaintDetails from './pages/ComplaintDetails';
import AdminDashboard from './pages/AdminDashboard';
import AdminComplaintsManager from './pages/AdminComplaintsManager';
import ComplaintTimeline from './pages/ComplaintTimeline';
import AdminReports from './pages/AdminReports';
import './App.css';

const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/" />;
};

const AdminRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('userRole');
  
  if (!token) {
    return <Navigate to="/" />;
  }
  
  if (role !== 'admin') {
    return <Navigate to="/dashboard" />;
  }
  
  return children;
};

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<RoleSelection />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/submit"
            element={
              <PrivateRoute>
                <SubmitComplaint />
              </PrivateRoute>
            }
          />
          <Route
            path="/complaint/:id"
            element={
              <PrivateRoute>
                <ComplaintDetails />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminDashboard />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/complaints"
            element={
              <AdminRoute>
                <AdminComplaintsManager />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/complaints/:complaintId/timeline"
            element={
              <AdminRoute>
                <ComplaintTimeline />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/reports"
            element={
              <AdminRoute>
                <AdminReports />
              </AdminRoute>
            }
          />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
