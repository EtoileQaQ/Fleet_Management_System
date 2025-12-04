import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { vehiclesApi } from '../api/vehicles';
import { telematicsApi } from '../api/telematics';
import {
  Truck,
  Plus,
  Search,
  Filter,
  Edit2,
  Trash2,
  X,
  CheckCircle2,
  Wrench,
  AlertCircle,
  Loader2,
  Wifi,
  WifiOff,
  Gauge,
} from 'lucide-react';
import './DataPages.css';

function Vehicles() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [formData, setFormData] = useState({
    registration_plate: '',
    vin: '',
    brand: '',
    model: '',
    status: 'ACTIVE',
  });

  const queryClient = useQueryClient();
  const hasWritePermission = useAuthStore((state) => state.hasWritePermission());

  const { data: vehicles = [], isLoading } = useQuery({
    queryKey: ['vehicles', statusFilter],
    queryFn: () => vehiclesApi.list(statusFilter ? { status: statusFilter } : {}),
  });

  // Get real-time status for all vehicles
  const { data: vehicleStatuses = [] } = useQuery({
    queryKey: ['vehicleStatuses'],
    queryFn: () => telematicsApi.getAllVehiclesStatus(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Merge vehicle data with real-time status
  const vehiclesWithStatus = vehicles.map(vehicle => {
    const status = vehicleStatuses.find(s => s.id === vehicle.id);
    return {
      ...vehicle,
      is_online: status?.is_online || false,
      last_seen: status?.last_seen,
      current_speed: status?.current_speed,
    };
  });

  const createMutation = useMutation({
    mutationFn: vehiclesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['vehicles']);
      closeModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => vehiclesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['vehicles']);
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: vehiclesApi.delete,
    onSuccess: () => queryClient.invalidateQueries(['vehicles']),
  });

  const filteredVehicles = vehiclesWithStatus.filter(
    (v) =>
      v.registration_plate.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.brand.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.model.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const openCreateModal = () => {
    setEditingVehicle(null);
    setFormData({
      registration_plate: '',
      vin: '',
      brand: '',
      model: '',
      status: 'ACTIVE',
    });
    setShowModal(true);
  };

  const openEditModal = (vehicle) => {
    setEditingVehicle(vehicle);
    setFormData({
      registration_plate: vehicle.registration_plate,
      vin: vehicle.vin,
      brand: vehicle.brand,
      model: vehicle.model,
      status: vehicle.status,
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingVehicle(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingVehicle) {
      updateMutation.mutate({ id: editingVehicle.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this vehicle?')) {
      deleteMutation.mutate(id);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ACTIVE':
        return <CheckCircle2 size={16} className="status-icon active" />;
      case 'MAINTENANCE':
        return <Wrench size={16} className="status-icon maintenance" />;
      default:
        return <AlertCircle size={16} className="status-icon inactive" />;
    }
  };

  return (
    <div className="data-page">
      {/* Header */}
      <header className="page-header">
        <div className="header-content">
          <h1>
            <Truck size={28} />
            Vehicles
          </h1>
          <p>Manage your fleet vehicles</p>
        </div>
        {hasWritePermission && (
          <button className="btn-primary" onClick={openCreateModal}>
            <Plus size={20} />
            Add Vehicle
          </button>
        )}
      </header>

      {/* Filters */}
      <div className="filters-bar">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search vehicles..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <Filter size={18} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="ACTIVE">Active</option>
            <option value="MAINTENANCE">Maintenance</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        {isLoading ? (
          <div className="loading-state">
            <Loader2 size={32} className="animate-spin" />
            <p>Loading vehicles...</p>
          </div>
        ) : filteredVehicles.length === 0 ? (
          <div className="empty-state">
            <Truck size={48} />
            <h3>No vehicles found</h3>
            <p>
              {searchTerm || statusFilter
                ? 'Try adjusting your filters'
                : 'Add your first vehicle to get started'}
            </p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Registration</th>
                <th>Connection</th>
                <th>Brand</th>
                <th>Model</th>
                <th>Status</th>
                <th>Driver</th>
                {hasWritePermission && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {filteredVehicles.map((vehicle) => (
                <tr key={vehicle.id}>
                  <td className="mono">{vehicle.registration_plate}</td>
                  <td>
                    <span className={`online-badge ${vehicle.is_online ? 'online' : 'offline'}`}>
                      {vehicle.is_online ? (
                        <>
                          <Wifi size={14} />
                          <span>Online</span>
                          {vehicle.current_speed !== null && (
                            <span className="speed-indicator">
                              <Gauge size={12} />
                              {Math.round(vehicle.current_speed)} km/h
                            </span>
                          )}
                        </>
                      ) : (
                        <>
                          <WifiOff size={14} />
                          <span>Offline</span>
                        </>
                      )}
                    </span>
                  </td>
                  <td>{vehicle.brand}</td>
                  <td>{vehicle.model}</td>
                  <td>
                    <span className={`status-badge ${vehicle.status.toLowerCase()}`}>
                      {getStatusIcon(vehicle.status)}
                      {vehicle.status}
                    </span>
                  </td>
                  <td>
                    {vehicle.current_driver ? (
                      <span className="driver-badge">
                        {vehicle.current_driver.name}
                      </span>
                    ) : (
                      <span className="text-muted">Unassigned</span>
                    )}
                  </td>
                  {hasWritePermission && (
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn-icon"
                          onClick={() => openEditModal(vehicle)}
                          title="Edit"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          className="btn-icon danger"
                          onClick={() => handleDelete(vehicle.id)}
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingVehicle ? 'Edit Vehicle' : 'Add Vehicle'}</h2>
              <button className="btn-close" onClick={closeModal}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-grid">
                  <div className="form-group">
                    <label>Registration Plate</label>
                    <input
                      type="text"
                      value={formData.registration_plate}
                      onChange={(e) =>
                        setFormData({ ...formData, registration_plate: e.target.value })
                      }
                      placeholder="ABC-123"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>VIN (17 characters)</label>
                    <input
                      type="text"
                      value={formData.vin}
                      onChange={(e) =>
                        setFormData({ ...formData, vin: e.target.value })
                      }
                      placeholder="1HGBH41JXMN109186"
                      maxLength={17}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Brand</label>
                    <input
                      type="text"
                      value={formData.brand}
                      onChange={(e) =>
                        setFormData({ ...formData, brand: e.target.value })
                      }
                      placeholder="Toyota"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Model</label>
                    <input
                      type="text"
                      value={formData.model}
                      onChange={(e) =>
                        setFormData({ ...formData, model: e.target.value })
                      }
                      placeholder="Corolla"
                      required
                    />
                  </div>
                  <div className="form-group full-width">
                    <label>Status</label>
                    <select
                      value={formData.status}
                      onChange={(e) =>
                        setFormData({ ...formData, status: e.target.value })
                      }
                    >
                      <option value="ACTIVE">Active</option>
                      <option value="MAINTENANCE">Maintenance</option>
                      <option value="INACTIVE">Inactive</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      Saving...
                    </>
                  ) : editingVehicle ? (
                    'Update Vehicle'
                  ) : (
                    'Create Vehicle'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Vehicles;


