import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { driversApi } from '../api/drivers';
import { tachographApi } from '../api/tachograph';
import {
  Upload as UploadIcon,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Truck,
  Coffee,
  Briefcase,
  Loader2,
  X,
} from 'lucide-react';
import './Upload.css';

function Upload() {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedDriverId, setSelectedDriverId] = useState('');
  const [uploadResult, setUploadResult] = useState(null);
  
  const queryClient = useQueryClient();
  
  const { data: drivers = [] } = useQuery({
    queryKey: ['drivers'],
    queryFn: () => driversApi.list(),
  });
  
  const uploadMutation = useMutation({
    mutationFn: ({ file, driverId }) => tachographApi.upload(file, driverId),
    onSuccess: (data) => {
      setUploadResult(data);
      queryClient.invalidateQueries(['drivers']);
      if (data.success) {
        setSelectedFile(null);
      }
    },
    onError: (error) => {
      setUploadResult({
        success: false,
        filename: selectedFile?.name || 'unknown',
        errors: [error.response?.data?.detail || 'Upload failed']
      });
    }
  });
  
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);
  
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  }, []);
  
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };
  
  const validateAndSetFile = (file) => {
    const extension = file.name.split('.').pop().toLowerCase();
    if (!['ddd', 'tgd'].includes(extension)) {
      setUploadResult({
        success: false,
        filename: file.name,
        errors: ['Invalid file type. Only .DDD and .TGD files are allowed.']
      });
      return;
    }
    setSelectedFile(file);
    setUploadResult(null);
  };
  
  const handleUpload = () => {
    if (!selectedFile || !selectedDriverId) return;
    uploadMutation.mutate({ file: selectedFile, driverId: selectedDriverId });
  };
  
  const clearFile = () => {
    setSelectedFile(null);
    setUploadResult(null);
  };
  
  const getActivityIcon = (type) => {
    switch (type) {
      case 'DRIVING': return <Truck size={16} />;
      case 'REST':
      case 'BREAK': return <Coffee size={16} />;
      case 'WORK': return <Briefcase size={16} />;
      default: return <Clock size={16} />;
    }
  };
  
  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };
  
  return (
    <div className="upload-page">
      <header className="page-header">
        <div className="header-content">
          <h1>
            <UploadIcon size={28} />
            Tachograph Upload
          </h1>
          <p>Upload driver card (.DDD) or vehicle unit (.TGD) files</p>
        </div>
      </header>
      
      {/* Upload Area */}
      <div className="upload-container">
        <div className="upload-card">
          <div
            className={`drop-zone ${dragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFile ? (
              <div className="file-preview">
                <FileText size={48} />
                <div className="file-info">
                  <span className="file-name">{selectedFile.name}</span>
                  <span className="file-size">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <button className="clear-file" onClick={clearFile}>
                  <X size={20} />
                </button>
              </div>
            ) : (
              <>
                <div className="drop-icon">
                  <UploadIcon size={48} />
                </div>
                <p className="drop-text">
                  Drag and drop your tachograph file here
                </p>
                <p className="drop-hint">or</p>
                <label className="browse-btn">
                  Browse Files
                  <input
                    type="file"
                    accept=".ddd,.tgd,.DDD,.TGD"
                    onChange={handleFileChange}
                    hidden
                  />
                </label>
                <p className="file-types">Supported: .DDD, .TGD</p>
              </>
            )}
          </div>
          
          {/* Driver Selection */}
          <div className="upload-options">
            <div className="form-group">
              <label>Select Driver</label>
              <select
                value={selectedDriverId}
                onChange={(e) => setSelectedDriverId(e.target.value)}
                required
              >
                <option value="">Choose a driver...</option>
                {drivers.map((driver) => (
                  <option key={driver.id} value={driver.id}>
                    {driver.name} ({driver.license_number})
                  </option>
                ))}
              </select>
            </div>
            
            <button
              className="upload-btn"
              onClick={handleUpload}
              disabled={!selectedFile || !selectedDriverId || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <UploadIcon size={20} />
                  Upload & Process
                </>
              )}
            </button>
          </div>
        </div>
        
        {/* Upload Result */}
        {uploadResult && (
          <div className={`result-card ${uploadResult.success ? 'success' : 'error'}`}>
            <div className="result-header">
              {uploadResult.success ? (
                <>
                  <CheckCircle2 size={24} />
                  <h3>Upload Successful</h3>
                </>
              ) : (
                <>
                  <XCircle size={24} />
                  <h3>Upload Failed</h3>
                </>
              )}
            </div>
            
            <div className="result-content">
              <p className="result-filename">
                <FileText size={16} />
                {uploadResult.filename}
              </p>
              
              {uploadResult.success && (
                <div className="result-stats">
                  <div className="stat">
                    <span className="stat-value">{uploadResult.activities_created}</span>
                    <span className="stat-label">Activities Created</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{uploadResult.activities_skipped}</span>
                    <span className="stat-label">Skipped (Duplicates)</span>
                  </div>
                </div>
              )}
              
              {uploadResult.parse_result && uploadResult.success && (
                <div className="activity-summary">
                  <h4>Activity Summary</h4>
                  <div className="summary-grid">
                    <div className="summary-item driving">
                      <Truck size={20} />
                      <span>{formatDuration(uploadResult.parse_result.total_driving_minutes)}</span>
                      <label>Driving</label>
                    </div>
                    <div className="summary-item rest">
                      <Coffee size={20} />
                      <span>{formatDuration(uploadResult.parse_result.total_rest_minutes)}</span>
                      <label>Rest/Break</label>
                    </div>
                    <div className="summary-item work">
                      <Briefcase size={20} />
                      <span>{formatDuration(uploadResult.parse_result.total_work_minutes)}</span>
                      <label>Work</label>
                    </div>
                  </div>
                </div>
              )}
              
              {uploadResult.errors && uploadResult.errors.length > 0 && (
                <div className="error-list">
                  {uploadResult.errors.map((error, idx) => (
                    <div key={idx} className="error-item">
                      <AlertTriangle size={16} />
                      <span>{error}</span>
                    </div>
                  ))}
                </div>
              )}
              
              {uploadResult.parse_result?.warnings?.length > 0 && (
                <div className="warning-list">
                  {uploadResult.parse_result.warnings.map((warning, idx) => (
                    <div key={idx} className="warning-item">
                      <AlertTriangle size={16} />
                      <span>{warning}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Upload;


