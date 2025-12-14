import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { API_CONFIG } from '../../config';

// API endpoint
const API_ENDPOINT = API_CONFIG.API_ENDPOINT;

const DocumentUpload: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [source, setSource] = useState<'BANK' | 'COUNTERPARTY'>('BANK');
  const [tradeDateRange, setTradeDateRange] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Filter for PDF files only
    const pdfFiles = acceptedFiles.filter(
      file => file.type === 'application/pdf'
    );
    
    if (pdfFiles.length !== acceptedFiles.length) {
      alert('Only PDF files are accepted');
    }
    
    setFiles(prevFiles => [...prevFiles, ...pdfFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    }
  });

  const removeFile = (index: number) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setUploadStatus({
        success: false,
        message: 'Please select at least one file to upload',
      });
      return;
    }

    setUploading(true);
    setUploadStatus(null);

    try {
      // Process files one by one instead of all at once
      const uploadedKeys = [];
      
      for (const file of files) {
        try {
          console.log(`Requesting pre-signed URL for ${file.name}`);
          
          // Step 1: Get pre-signed URL from API
          const response = await fetch(`${API_ENDPOINT}/documents`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: JSON.stringify({
              fileName: file.name,
              source,
              tradeDateRange: tradeDateRange || 'unspecified',
            }),
            // Add mode for CORS
            mode: 'cors',
            credentials: 'omit'
          });
          
          // Log detailed information about the response
          console.log('Response status:', response.status);
          console.log('Response headers:', Object.fromEntries(response.headers.entries()));
          
          console.log('Pre-signed URL response status:', response.status);
          
          if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response body:', errorText);
            throw new Error(`Failed to get pre-signed URL: ${response.status} ${response.statusText}`);
          }
          
          const data = await response.json();
          console.log('Pre-signed URL response:', data);
          
          const { uploadUrl, key } = data;
          
          if (!uploadUrl) {
            throw new Error('No upload URL returned from server');
          }
          
          console.log(`Uploading file ${file.name} to S3 with URL:`, uploadUrl);
          
          // Step 2: Upload file directly to S3 using pre-signed URL
          const uploadResponse = await fetch(uploadUrl, {
            method: 'PUT',
            headers: {
              'Content-Type': file.type,
            },
            body: file,
          });
          
          console.log('S3 upload response status:', uploadResponse.status);
          
          if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            console.error('S3 error response:', errorText);
            throw new Error(`Failed to upload file: ${uploadResponse.status} ${uploadResponse.statusText}`);
          }
          
          console.log(`Successfully uploaded ${file.name} to S3`);
          uploadedKeys.push(key);
        } catch (fileError: any) {
          console.error(`Error uploading file ${file.name}:`, fileError);
          throw fileError; // Re-throw to be caught by the outer catch block
        }
      }
      
      console.log(`Successfully uploaded ${uploadedKeys.length} files`);
      
      // Set success status
      setUploadStatus({
        success: true,
        message: `Successfully uploaded ${files.length} file(s)`,
      });
      
      // Clear files after successful upload
      setFiles([]);
      
      // Refresh the dashboard data
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
    } catch (error: any) {
      console.error('Error uploading files:', error);
      let errorMessage = 'Error uploading files. Please try again.';
      
      // Extract more detailed error information for fetch API errors
      if (error.message) {
        errorMessage = `Error: ${error.message}`;
      }
      
      setUploadStatus({
        success: false,
        message: errorMessage,
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Document Upload</h1>
      
      {uploadStatus && (
        <div className={`mb-4 p-4 rounded-md ${uploadStatus.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
          {uploadStatus.message}
        </div>
      )}
      
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          {/* Source Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Document Source</label>
            <div className="flex space-x-4">
              <div className="flex items-center">
                <input
                  id="bank"
                  name="source"
                  type="radio"
                  checked={source === 'BANK'}
                  onChange={() => setSource('BANK')}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                />
                <label htmlFor="bank" className="ml-2 block text-sm text-gray-700">
                  Bank
                </label>
              </div>
              <div className="flex items-center">
                <input
                  id="counterparty"
                  name="source"
                  type="radio"
                  checked={source === 'COUNTERPARTY'}
                  onChange={() => setSource('COUNTERPARTY')}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                />
                <label htmlFor="counterparty" className="ml-2 block text-sm text-gray-700">
                  Counterparty
                </label>
              </div>
            </div>
          </div>
          
          {/* Optional Metadata */}
          <div className="mb-6">
            <label htmlFor="tradeDateRange" className="block text-sm font-medium text-gray-700 mb-2">
              Trade Date Range (optional)
            </label>
            <input
              type="text"
              id="tradeDateRange"
              placeholder="e.g., 2025-07-01 to 2025-07-18"
              value={tradeDateRange}
              onChange={(e) => setTradeDateRange(e.target.value)}
              className="input"
            />
          </div>
          
          {/* File Upload Dropzone */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Upload PDF Documents</label>
            <div
              {...getRootProps()}
              className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md ${
                isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'
              }`}
            >
              <div className="space-y-1 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                  aria-hidden="true"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className="flex text-sm text-gray-600">
                  <input {...getInputProps()} />
                  <p className="pl-1">Drag and drop PDF files here, or click to select files</p>
                </div>
                <p className="text-xs text-gray-500">PDF files only</p>
              </div>
            </div>
          </div>
          
          {/* File List */}
          {files.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Selected Files</h3>
              <ul className="border border-gray-200 rounded-md divide-y divide-gray-200">
                {files.map((file, index) => (
                  <li key={index} className="pl-3 pr-4 py-3 flex items-center justify-between text-sm">
                    <div className="w-0 flex-1 flex items-center">
                      <svg className="flex-shrink-0 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                      </svg>
                      <span className="ml-2 flex-1 w-0 truncate">{file.name}</span>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="font-medium text-red-600 hover:text-red-500"
                      >
                        Remove
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Upload Button */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading || files.length === 0}
              className={`btn-primary ${
                uploading || files.length === 0 ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {uploading ? 'Uploading...' : 'Upload Documents'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
