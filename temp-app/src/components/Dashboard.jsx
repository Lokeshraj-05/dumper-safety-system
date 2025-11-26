import React, { useState } from 'react';
import './Dashboard.css';
import ImageUpload from './ImageUpload';
import VideoUpload from './VideoUpload';

export default function Dashboard({ username, onLogout }) {
  const [activeTab, setActiveTab] = useState('image');
  const [detectionResults, setDetectionResults] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [videoResults, setVideoResults] = useState(null);
  const [loading, setLoading] = useState(false);

  // IMAGE HANDLERS
  const handleImageUpload = async (file) => {
    setUploadedImage(file);
    setDetectionResults(null);
  };

  const handleDetect = async () => {
    if (!uploadedImage) {
      alert('Please upload an image first');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadedImage);

      const response = await fetch('http://localhost:8000/detect/image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        setDetectionResults(data);
      } else {
        alert('Detection failed: ' + data.error);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setUploadedImage(null);
    setDetectionResults(null);
  };

  // VIDEO HANDLERS
  const handleVideoUpload = (file) => {
    setVideoFile(file);
    setVideoResults(null);
  };

  const handleVideoDetect = async () => {
    if (!videoFile) {
      alert('Please upload a video first');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', videoFile);

      const response = await fetch('http://localhost:8000/detect/video', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        setVideoResults(data);
      } else {
        alert('Video detection failed: ' + data.error);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClearVideo = () => {
    setVideoFile(null);
    setVideoResults(null);
  };

  // Utility
  const getHazardColor = (level) => {
    const colors = {
      'LOW': '#28a745',
      'MEDIUM': '#ffc107',
      'HIGH': '#fd7e14',
      'CRITICAL': '#dc3545'
    };
    return colors[level] || '#6c757d';
  };

  const getHazardLevelFromScore = (score) => {
    if (score >= 75) return 'CRITICAL';
    if (score >= 50) return 'HIGH';
    if (score >= 25) return 'MEDIUM';
    return 'LOW';
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1 className="header-title">🛡️ HALO</h1>
        </div>
        <div className="header-right">
          <span className="user-info">👤 {username}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="dashboard-tabs">
        <button
          className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
          onClick={() => setActiveTab('image')}
        >
          📷 Image Detection
        </button>
        <button
          className={`tab-btn ${activeTab === 'video' ? 'active' : ''}`}
          onClick={() => setActiveTab('video')}
        >
          🎬 Video Detection
        </button>
      </div>

      {/* Main Content */}
      <div className="dashboard-content">
        {activeTab === 'image' && (
          <div className="image-detection-section">
            {/* Left Column - Upload & Preview */}
            <div className="upload-panel">
              <h2>Upload Construction Site Image</h2>
              
              <ImageUpload onFileSelect={handleImageUpload} />

              {uploadedImage && (
                <div className="preview-section">
                  <p className="preview-label">📁 {uploadedImage.name}</p>
                  <div className="preview-container">
                    <img
                      src={URL.createObjectURL(uploadedImage)}
                      alt="Preview"
                      className="preview-image"
                    />
                  </div>
                </div>
              )}

              <div className="action-buttons">
                <button
                  onClick={handleDetect}
                  disabled={!uploadedImage || loading}
                  className="detect-btn"
                >
                  {loading ? '⏳ Detecting...' : '🔍 Detect Objects'}
                </button>
                {uploadedImage && (
                  <button onClick={handleClear} className="clear-btn">
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Right Column - Results */}
            <div className="results-panel">
              {detectionResults ? (
                <div className="results-container">
                  <h2>Detection Results</h2>

                  {/* Summary Stats */}
                  <div className="results-summary">
                    <div className="stat-box">
                      <span className="stat-label">Total Objects</span>
                      <span className="stat-value">{detectionResults.summary.total_objects}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Max Hazard</span>
                      <span
                        className="stat-value stat-hazard"
                        style={{ color: getHazardColor(
                          detectionResults.detections.length > 0 
                            ? detectionResults.detections.reduce((max, d) => d.hazard_score > max.hazard_score ? d : max).hazard_level
                            : 'LOW'
                        )}}
                      >
                        {detectionResults.summary.max_hazard_score}
                      </span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Classes</span>
                      <span className="stat-value">{detectionResults.summary.classes_detected.join(', ')}</span>
                    </div>
                  </div>

                  {/* Detections List */}
                  <div className="detections-list">
                    {detectionResults.detections.map((det, idx) => (
                      <div key={idx} className="detection-card">
                        <div className="detection-header">
                          <span className="detection-class">{det.class}</span>
                          <span
                            className="detection-hazard-badge"
                            style={{ backgroundColor: getHazardColor(det.hazard_level) }}
                          >
                            {det.hazard_level}
                          </span>
                        </div>
                        <div className="detection-body">
                          <div className="detection-row">
                            <span>Confidence:</span>
                            <div className="confidence-bar">
                              <div
                                className="confidence-fill"
                                style={{ width: `${det.confidence * 100}%` }}
                              />
                              <span>{(det.confidence * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                          <div className="detection-row">
                            <span>Hazard Score:</span>
                            <strong>{det.hazard_score}</strong>
                          </div>
                          <div className="detection-row">
                            <span>Distance:</span>
                            <strong>{det.estimated_distance}</strong>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="no-results">
                  <p>👆 Upload an image and click "Detect Objects" to see results</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'video' && (
          <div className="image-detection-section">
            {/* Left Column - Video Upload */}
            <div className="upload-panel">
              <h2>Upload Construction Site Video</h2>
              
              <VideoUpload onFileSelect={handleVideoUpload} />

              {videoFile && (
                <div className="preview-section">
                  <p className="preview-label">📁 {videoFile.name}</p>
                  <div className="video-info-box">
                    <p>Size: {(videoFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                    <p>Type: {videoFile.type}</p>
                  </div>
                </div>
              )}

              <div className="action-buttons">
                <button
                  onClick={handleVideoDetect}
                  disabled={!videoFile || loading}
                  className="detect-btn"
                >
                  {loading ? '⏳ Analyzing Video...' : '🎬 Analyze Video'}
                </button>
                {videoFile && (
                  <button onClick={handleClearVideo} className="clear-btn">
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Right Column - Video Results */}
            <div className="results-panel">
              {videoResults ? (
                <div className="results-container">
                  <h2>Video Analysis Results</h2>

                  {/* Video Summary Stats */}
                  <div className="results-summary">
                    <div className="stat-box">
                      <span className="stat-label">Total Frames</span>
                      <span className="stat-value">{videoResults.videoinfo.totalframes}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Analyzed Frames</span>
                      <span className="stat-value">{videoResults.videoinfo.processedframes}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">FPS</span>
                      <span className="stat-value">{videoResults.videoinfo.fps}</span>
                    </div>
                  </div>

                  <h3 className="section-title">Frame-by-Frame Detection</h3>
                  
                  {/* Frame Results Grid */}
                  <div className="detections-list">
                    {videoResults.frameresults.map((frame, idx) => {
                      const hazardLevel = getHazardLevelFromScore(frame.maxhazard);
                      return (
                        <div key={idx} className="detection-card">
                          <div className="detection-header">
                            <span className="detection-class">🎞️ Frame {frame.frame}</span>
                            <span
                              className="detection-hazard-badge"
                              style={{ backgroundColor: getHazardColor(hazardLevel) }}
                            >
                              {hazardLevel}
                            </span>
                          </div>
                          <div className="detection-body">
                            <div className="detection-row">
                              <span>Timestamp:</span>
                              <strong>{frame.timestamp}s</strong>
                            </div>
                            <div className="detection-row">
                              <span>Objects Detected:</span>
                              <strong>{frame.detections}</strong>
                            </div>
                            <div className="detection-row">
                              <span>Hazard Score:</span>
                              <strong style={{ color: getHazardColor(hazardLevel) }}>
                                {frame.maxhazard}
                              </strong>
                            </div>
                            {frame.details && frame.details.classes && (
                              <div className="detection-row">
                                <span>Classes:</span>
                                <strong>{frame.details.classes.join(', ')}</strong>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="no-results">
                  <p>👆 Upload a video and click "Analyze Video" to see frame-by-frame detection results</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
