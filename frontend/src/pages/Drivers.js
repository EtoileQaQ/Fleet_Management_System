import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { driversApi } from '../api/drivers';
import { vehiclesApi } from '../api/vehicles';
import {
  Users,
  Plus,
  Search,
  Edit2,
  Trash2,
  X,
  Truck,
  Link2,
  Unlink,
  Loader2,
  CreditCard,
} from 'lucide-react';
import './DataPages.css';

function Drivers() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [editingDriver, setEditingDriver] = useState(null);
  const [assigningDriver, setAssigningDriver] = useState(null);
  const [selectedVehicleId, setSelectedVehicleId] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    license_number: '',
    rfid_tag: '',
    timezone: 'UTC',
  });

  const queryClient = useQueryClient();
  const hasWritePermission = useAuthStore((state) => state.hasWritePermission());

  const { data: drivers = [], isLoading } = useQuery({
    queryKey: ['drivers'],
    queryFn: () => driversApi.list(),
  });

  const { data: vehicles = [] } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => vehiclesApi.list(),
  });

  const availableVehicles = vehicles.filter(
    (v) => !v.current_driver || v.current_driver?.id === assigningDriver?.current_vehicle_id
  );

  const createMutation = useMutation({
    mutationFn: driversApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['drivers']);
      closeModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => driversApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['drivers']);
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: driversApi.delete,
    onSuccess: () => queryClient.invalidateQueries(['drivers']),
  });

  const assignMutation = useMutation({
    mutationFn: ({ driverId, vehicleId }) => driversApi.assignVehicle(driverId, vehicleId),
    onSuccess: () => {
      queryClient.invalidateQueries(['drivers']);
      queryClient.invalidateQueries(['vehicles']);
      closeAssignModal();
    },
  });

  const unassignMutation = useMutation({
    mutationFn: driversApi.unassignVehicle,
    onSuccess: () => {
      queryClient.invalidateQueries(['drivers']);
      queryClient.invalidateQueries(['vehicles']);
    },
  });

  const filteredDrivers = drivers.filter(
    (d) =>
      d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.license_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const openCreateModal = () => {
    setEditingDriver(null);
    setFormData({
      name: '',
      license_number: '',
      rfid_tag: '',
      timezone: 'UTC',
    });
    setShowModal(true);
  };

  const openEditModal = (driver) => {
    setEditingDriver(driver);
    setFormData({
      name: driver.name,
      license_number: driver.license_number,
      rfid_tag: driver.rfid_tag || '',
      timezone: driver.timezone,
    });
    setShowModal(true);
  };

  const openAssignModal = (driver) => {
    setAssigningDriver(driver);
    setSelectedVehicleId(driver.current_vehicle_id || '');
    setShowAssignModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingDriver(null);
  };

  const closeAssignModal = () => {
    setShowAssignModal(false);
    setAssigningDriver(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingDriver) {
      updateMutation.mutate({ id: editingDriver.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleAssign = (e) => {
    e.preventDefault();
    if (selectedVehicleId) {
      assignMutation.mutate({
        driverId: assigningDriver.id,
        vehicleId: parseInt(selectedVehicleId),
      });
    }
  };

  const handleUnassign = (driverId) => {
    if (window.confirm('Unassign this driver from their vehicle?')) {
      unassignMutation.mutate(driverId);
    }
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this driver?')) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="data-page">
      {/* Header */}
      <header className="page-header">
        <div className="header-content">
          <h1>
            <Users size={28} />
            Drivers
          </h1>
          <p>Manage your fleet drivers</p>
        </div>
        {hasWritePermission && (
          <button className="btn-primary" onClick={openCreateModal}>
            <Plus size={20} />
            Add Driver
          </button>
        )}
      </header>

      {/* Filters */}
      <div className="filters-bar">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search drivers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        {isLoading ? (
          <div className="loading-state">
            <Loader2 size={32} className="animate-spin" />
            <p>Loading drivers...</p>
          </div>
        ) : filteredDrivers.length === 0 ? (
          <div className="empty-state">
            <Users size={48} />
            <h3>No drivers found</h3>
            <p>
              {searchTerm
                ? 'Try adjusting your search'
                : 'Add your first driver to get started'}
            </p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>License Number</th>
                <th>RFID Tag</th>
                <th>Timezone</th>
                <th>Assigned Vehicle</th>
                {hasWritePermission && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {filteredDrivers.map((driver) => (
                <tr key={driver.id}>
                  <td className="driver-name">
                    <div className="driver-avatar">
                      {driver.name.charAt(0).toUpperCase()}
                    </div>
                    {driver.name}
                  </td>
                  <td className="mono">{driver.license_number}</td>
                  <td>
                    {driver.rfid_tag ? (
                      <span className="rfid-badge">
                        <CreditCard size={14} />
                        {driver.rfid_tag}
                      </span>
                    ) : (
                      <span className="text-muted">Not set</span>
                    )}
                  </td>
                  <td>{driver.timezone}</td>
                  <td>
                    {driver.current_vehicle ? (
                      <span className="vehicle-badge">
                        <Truck size={14} />
                        {driver.current_vehicle.registration_plate}
                      </span>
                    ) : (
                      <span className="text-muted">Unassigned</span>
                    )}
                  </td>
                  {hasWritePermission && (
                    <td>
                      <div className="action-buttons">
                        {driver.current_vehicle ? (
                          <button
                            className="btn-icon warning"
                            onClick={() => handleUnassign(driver.id)}
                            title="Unassign Vehicle"
                          >
                            <Unlink size={16} />
                          </button>
                        ) : (
                          <button
                            className="btn-icon success"
                            onClick={() => openAssignModal(driver)}
                            title="Assign Vehicle"
                          >
                            <Link2 size={16} />
                          </button>
                        )}
                        <button
                          className="btn-icon"
                          onClick={() => openEditModal(driver)}
                          title="Edit"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          className="btn-icon danger"
                          onClick={() => handleDelete(driver.id)}
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

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingDriver ? 'Edit Driver' : 'Add Driver'}</h2>
              <button className="btn-close" onClick={closeModal}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-grid">
                  <div className="form-group">
                    <label>Full Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      placeholder="John Doe"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>License Number</label>
                    <input
                      type="text"
                      value={formData.license_number}
                      onChange={(e) =>
                        setFormData({ ...formData, license_number: e.target.value })
                      }
                      placeholder="DL-123456"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>RFID Tag (Optional)</label>
                    <input
                      type="text"
                      value={formData.rfid_tag}
                      onChange={(e) =>
                        setFormData({ ...formData, rfid_tag: e.target.value })
                      }
                      placeholder="RFID-001"
                    />
                  </div>
                  <div className="form-group">
                    <label>Timezone</label>
                    <select
                      value={formData.timezone}
                      onChange={(e) =>
                        setFormData({ ...formData, timezone: e.target.value })
                      }
                    >
                      <option value="UTC">UTC</option>
                      <option value="Europe/Paris">Europe/Paris</option>
                      <option value="Europe/London">Europe/London</option>
                      <option value="America/New_York">America/New_York</option>
                      <option value="America/Los_Angeles">America/Los_Angeles</option>
                      <option value="Asia/Tokyo">Asia/Tokyo</option>
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
                  ) : editingDriver ? (
                    'Update Driver'
                  ) : (
                    'Create Driver'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Vehicle Modal */}
      {showAssignModal && (
        <div className="modal-overlay" onClick={closeAssignModal}>
          <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Assign Vehicle</h2>
              <button className="btn-close" onClick={closeAssignModal}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAssign}>
              <div className="modal-body">
                <p className="modal-subtitle">
                  Assign a vehicle to <strong>{assigningDriver?.name}</strong>
                </p>
                <div className="form-group">
                  <label>Select Vehicle</label>
                  <select
                    value={selectedVehicleId}
                    onChange={(e) => setSelectedVehicleId(e.target.value)}
                    required
                  >
                    <option value="">Choose a vehicle...</option>
                    {availableVehicles.map((vehicle) => (
                      <option key={vehicle.id} value={vehicle.id}>
                        {vehicle.registration_plate} - {vehicle.brand} {vehicle.model}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={closeAssignModal}>
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={assignMutation.isPending || !selectedVehicleId}
                >
                  {assignMutation.isPending ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      Assigning...
                    </>
                  ) : (
                    'Assign Vehicle'
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

export default Drivers;



