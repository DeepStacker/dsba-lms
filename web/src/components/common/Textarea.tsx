import React from 'react';
import { Field, Label, Textarea as HeadlessTextarea, Description } from '@headlessui/react';

interface TextareaProps {
  label?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  description?: string;
  rows?: number;
  className?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
  error,
  description,
  rows = 4,
  className = '',
}) => {
  return (
    <Field className={className}>
      {label && (
        <Label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </Label>
      )}
      <HeadlessTextarea
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        rows={rows}
        className={`block w-full rounded-md shadow-sm focus:ring-2 focus:ring-offset-2 disabled:bg-gray-50 disabled:text-gray-500 ${
          error
            ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
            : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
        }`}
      />
      {description && !error && (
        <Description className="mt-1 text-sm text-gray-500">{description}</Description>
      )}
      {error && (
        <Description className="mt-1 text-sm text-red-600">{error}</Description>
      )}
    </Field>
  );
};