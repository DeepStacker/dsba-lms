import React, { useRef, useState } from 'react';
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon, PhotoIcon } from '@heroicons/react/24/outline';

interface FileUploadProps {
  label?: string;
  onFileSelect: (files: FileList | null) => void;
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // in MB
  error?: string;
  helperText?: string;
  disabled?: boolean;
  className?: string;
  value?: File[];
  initialFiles?: string[]; // URLs for initial preview
}

export const FileUpload: React.FC<FileUploadProps> = ({
  label,
  onFileSelect,
  accept,
  multiple = false,
  maxSize = 10,
  error,
  helperText,
  disabled = false,
  className = '',
  value = [],
  initialFiles = [],
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<File[]>(value);

  const handleFiles = (fileList: FileList | null) => {
    if (fileList) {
      const filesArray = Array.from(fileList);
      const validFiles: File[] = [];

      filesArray.forEach((file) => {
        if (file.size <= maxSize * 1024 * 1024) {
          validFiles.push(file);
        }
      });

      if (multiple) {
        const newFiles = [...files, ...validFiles];
        setFiles(newFiles);
        onFileSelect(Array.from(validFiles) as any);
      } else {
        setFiles(validFiles);
        onFileSelect(validFiles as any);
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (!disabled && e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleInputClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    onFileSelect(newFiles as any);
  };

  const getFileIcon = (fileName: string, mimeType?: string) => {
    if (mimeType?.startsWith('image/') || fileName.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/i)) {
      return <PhotoIcon className="h-8 w-8 text-blue-500" />;
    }
    return <DocumentIcon className="h-8 w-8 text-gray-500" />;
  };

  const formatFileSize = (size: number) => {
    if (size < 1024) return size + ' B';
    if (size < 1024 * 1024) return Math.round(size / 1024) + ' KB';
    return Math.round(size / (1024 * 1024)) + ' MB';
  };

  return (
    <div className={`space-y-1 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}

      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleInputClick}
        className={`relative border-2 border-dashed rounded-lg p-6 transition-colors cursor-pointer ${
          dragActive
            ? 'border-blue-400 bg-blue-50'
            : error
            ? 'border-red-300 hover:border-red-400'
            : 'border-gray-300 hover:border-gray-400'
        } ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept={accept}
          multiple={multiple}
          onChange={(e) => handleFiles(e.target.files)}
          disabled={disabled}
        />

        <div className="text-center">
          <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
          <div className="mt-2">
            <p className="text-sm text-gray-600">
              <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {accept ? `Accepted formats: ${accept}` : 'Any file type'}
              {maxSize && ` • Max ${maxSize}MB per file`}
              {multiple && ' • Multiple files allowed'}
            </p>
          </div>
        </div>
      </div>

      {/* Selected files preview */}
      {files.length > 0 && (
        <div className="space-y-2 mt-4">
          {files.map((file, index) => (
            <div key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
              {getFileIcon(file.name, file.type)}
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
              </div>
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="ml-2 text-gray-400 hover:text-red-500"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Initial files preview */}
      {initialFiles.length > 0 && files.length === 0 && (
        <div className="space-y-2 mt-4">
          {initialFiles.map((fileUrl, index) => {
            const fileName = fileUrl.split('/').pop() || 'File';
            return (
              <div key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                {getFileIcon(fileName)}
                <div className="ml-3 flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{fileName}</p>
                  <p className="text-xs text-gray-500">Existing file</p>
                </div>
                {!disabled && (
                  <button
                    type="button"
                    onClick={() => {}} // Handle removal
                    className="ml-2 text-gray-400 hover:text-red-500"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {(error || helperText) && (
        <p className={`text-sm ${error ? 'text-red-600' : 'text-gray-500'}`}>
          {error || helperText}
        </p>
      )}
    </div>
  );
};
