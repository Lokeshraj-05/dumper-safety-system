import React, { useRef } from 'react';

export default function ImageUpload({ onFileSelect }) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onFileSelect(file);
    } else {
      alert('Please select a valid image file');
    }
  };

  const handleDragDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const file = e.dataTransfer?.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onFileSelect(file);
    }
  };

  return (
    <div 
      className="upload-area"
      onClick={() => fileInputRef.current?.click()}
      onDrop={handleDragDrop}
      onDragOver={(e) => e.preventDefault()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
      <div className="upload-content">
        <span className="upload-icon">📤</span>
        <p>Click to upload or drag and drop</p>
        <p className="upload-hint">PNG, JPG, GIF (max 10MB)</p>
      </div>
    </div>
  );
}
