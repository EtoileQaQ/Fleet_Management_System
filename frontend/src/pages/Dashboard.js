import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { vehiclesApi } from '../api/vehicles';
import { driversApi } from '../api/drivers';
import { telematicsApi } from '../api/telematics';
import {
  Truck,
  Users,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Wrench,
  TrendingUp,
  Clock,
  Wifi,
  WifiOff,
} from 'lucide-react';
import './Dashboard.css';

function Dashboard() {
  const user = useAuthStore((state) => state.user);
  
  const { data: vehicles = [] } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => vehiclesApi.list(),
  });
  
  const { data: drivers = [] } = useQuery({
    queryKey: ['drivers'],
    queryFn: () => driversApi.list(),
  });

  const { data: onlineStats = { online: 0, offline: 0, total: 0 } } = useQuery({
    queryKey: ['onlineStats'],
    queryFn: () => telematicsApi.getOnlineStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const activeVehicles = vehicles.filter((v) => v.status === 'ACTIVE').length;
  const maintenanceVehicles = vehicles.filter((v) => v.status === 'MAINTENANCE').length;
  const assignedDrivers = drivers.filter((d) => d.current_vehicle_id).length;

  const stats = [
    {
      title: 'Total Vehicles',
      value: vehicles.length,
      icon: Truck,
      color: 'cyan',
      change: '+12%',
    },
    {
      title: 'Online Now',
      value: onlineStats.online,
      icon: Wifi,
      color: 'green',
      change: `${onlineStats.total ? Math.round((onlineStats.online / onlineStats.total) * 100) : 0}% connected`,
    },
    {
      title: 'In Maintenance',
      value: maintenanceVehicles,
      icon: Wrench,
      color: 'amber',
      change: maintenanceVehicles > 0 ? 'Attention' : 'All good',
    },
    {
      title: 'Total Drivers',
      value: drivers.length,
      icon: Users,
      color: 'purple',
      change: `${assignedDrivers} assigned`,
    },
  ];

  const recentActivity = [
    { type: 'vehicle', action: 'Vehicle ABC-123 marked as active', time: '2 min ago' },
    { type: 'driver', action: 'New driver John Doe added', time: '15 min ago' },
    { type: 'maintenance', action: 'Vehicle XYZ-789 sent to maintenance', time: '1 hour ago' },
    { type: 'assignment', action: 'Driver Jane Smith assigned to VEH-001', time: '2 hours ago' },
  ];

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Dashboard</h1>
          <p>Welcome back, {user?.email?.split('@')[0] || 'User'}</p>
        </div>
        <div className="header-badge">
          <span className="badge-dot"></span>
          <span>System Online</span>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div
            key={stat.title}
            className={`stat-card stat-${stat.color}`}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="stat-icon">
              <stat.icon size={24} />
            </div>
            <div className="stat-content">
              <span className="stat-value">{stat.value}</span>
              <span className="stat-title">{stat.title}</span>
            </div>
            <div className="stat-change">
              <TrendingUp size={14} />
              <span>{stat.change}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Fleet Overview */}
        <div className="dashboard-card fleet-overview">
          <div className="card-header">
            <h2>
              <Activity size={20} />
              Fleet Overview
            </h2>
          </div>
          <div className="card-content">
            <div className="overview-chart">
              <div className="chart-bar">
                <div
                  className="bar-fill active"
                  style={{ width: `${vehicles.length ? (activeVehicles / vehicles.length) * 100 : 0}%` }}
                ></div>
                <div
                  className="bar-fill maintenance"
                  style={{ width: `${vehicles.length ? (maintenanceVehicles / vehicles.length) * 100 : 0}%` }}
                ></div>
              </div>
              <div className="chart-legend">
                <div className="legend-item">
                  <span className="legend-dot active"></span>
                  <span>Active ({activeVehicles})</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot maintenance"></span>
                  <span>Maintenance ({maintenanceVehicles})</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot inactive"></span>
                  <span>Inactive ({vehicles.length - activeVehicles - maintenanceVehicles})</span>
                </div>
              </div>
            </div>
            
            {vehicles.length === 0 && (
              <div className="empty-state">
                <Truck size={48} />
                <p>No vehicles yet. Add your first vehicle to get started.</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="dashboard-card recent-activity">
          <div className="card-header">
            <h2>
              <Clock size={20} />
              Recent Activity
            </h2>
          </div>
          <div className="card-content">
            <div className="activity-list">
              {recentActivity.map((activity, index) => (
                <div key={index} className="activity-item">
                  <div className={`activity-icon ${activity.type}`}>
                    {activity.type === 'vehicle' && <Truck size={16} />}
                    {activity.type === 'driver' && <Users size={16} />}
                    {activity.type === 'maintenance' && <Wrench size={16} />}
                    {activity.type === 'assignment' && <CheckCircle2 size={16} />}
                  </div>
                  <div className="activity-content">
                    <span className="activity-action">{activity.action}</span>
                    <span className="activity-time">{activity.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Alerts */}
        <div className="dashboard-card alerts-card">
          <div className="card-header">
            <h2>
              <AlertTriangle size={20} />
              Alerts
            </h2>
          </div>
          <div className="card-content">
            {maintenanceVehicles > 0 ? (
              <div className="alert-item warning">
                <AlertTriangle size={20} />
                <div>
                  <strong>{maintenanceVehicles} vehicle(s)</strong> currently in maintenance
                </div>
              </div>
            ) : (
              <div className="alert-item success">
                <CheckCircle2 size={20} />
                <div>All vehicles are operational</div>
              </div>
            )}
            
            {drivers.length > 0 && drivers.length > vehicles.length && (
              <div className="alert-item info">
                <Users size={20} />
                <div>More drivers than vehicles available</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;


