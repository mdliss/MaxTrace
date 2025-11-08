import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUploadUrl, getDetectUrl } from '../config/api';

function Upload() {
  const [sessionId] = useState(`session-${Math.random().toString(36).substr(2, 9)}`);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];

  const validateFile = (file) => {
    if (!file) {
      return 'No file selected';
    }

    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Invalid file type. Please upload PNG, JPG, or PDF files only.';
    }

    if (file.size > MAX_FILE_SIZE) {
      return 'File size exceeds 10MB limit.';
    }

    return null;
  };

  const handleFileSelect = (file) => {
    setError(null);

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSelectedFile(file);

    // Create preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(file);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      // Step 1: Get presigned URL from backend
      setUploadProgress(10);
      const uploadResponse = await fetch(getUploadUrl(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fileName: selectedFile.name,
          fileType: selectedFile.type,
          fileSize: selectedFile.size,
          sessionId: sessionId,
        }),
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload request failed: ${uploadResponse.statusText}`);
      }

      const uploadData = await uploadResponse.json();
      const { uploadUrl, blueprintId, s3Key } = uploadData;

      // Step 2: Upload file to S3 using presigned URL
      setUploadProgress(30);
      const s3Response = await fetch(uploadUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': selectedFile.type,
        },
        body: selectedFile,
      });

      if (!s3Response.ok) {
        throw new Error(`S3 upload failed: ${s3Response.statusText}`);
      }

      // Step 3: Trigger inference
      setUploadProgress(70);
      const detectResponse = await fetch(getDetectUrl(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          blueprintId,
          sessionId,
          s3Key,
        }),
      });

      if (!detectResponse.ok) {
        throw new Error(`Detection request failed: ${detectResponse.statusText}`);
      }

      setUploadProgress(100);

      // Navigate to processing page to show real-time status
      setTimeout(() => {
        navigate(`/processing/${blueprintId}`);
      }, 500);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Upload failed. Please try again.');
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setUploadProgress(0);
    setIsUploading(false);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-gray-900">Innergy Room Detection AI</h1>
          <p className="text-sm text-gray-500">Session: {sessionId}</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Upload Blueprint</h2>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              isDragging
                ? 'border-blue-500 bg-blue-50'
                : selectedFile
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-blue-500'
            }`}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {!selectedFile ? (
              <div className="space-y-2">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className="text-gray-600">
                  <label htmlFor="file-upload" className="relative cursor-pointer rounded-md font-medium text-blue-600 hover:text-blue-500">
                    <span>Upload a file</span>
                    <input
                      ref={fileInputRef}
                      id="file-upload"
                      name="file-upload"
                      type="file"
                      className="sr-only"
                      accept=".png,.jpg,.jpeg,.pdf"
                      onChange={handleFileInputChange}
                    />
                  </label>
                  <p className="pl-1 inline">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">PNG, JPG, PDF up to 10MB</p>
              </div>
            ) : (
              <div className="space-y-4">
                {previewUrl && (
                  <img
                    src={previewUrl}
                    alt="Blueprint preview"
                    className="max-h-64 mx-auto rounded border border-gray-300"
                  />
                )}
                <div className="text-sm text-gray-700">
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-gray-500">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                  {selectedFile.type.startsWith('image/') && previewUrl && (
                    <p className="text-gray-500 text-xs mt-1">
                      Dimensions will be calculated after upload
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {isUploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          <div className="mt-6 flex gap-3">
            {selectedFile && !isUploading && (
              <>
                <button
                  onClick={handleUpload}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors font-medium"
                >
                  Process Blueprint
                </button>
                <button
                  onClick={handleReset}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors font-medium"
                >
                  Reset
                </button>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default Upload;
