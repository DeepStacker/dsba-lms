import React, { forwardRef } from 'react';
import { Input as HeadlessInput } from '@headlessui/react';
import { ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface InputProps {
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onBlur?: () => void;
  onFocus?: () => void;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
  disabled?: boolean;
  required?: boolean;
  error?: string;
  success?: string;
  helpText?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'filled' | 'outlined';
  leftIcon?: React.ComponentType<{ className?: string }>;
  rightIcon?: React.ComponentType<{ className?: string }>;
  autoFocus?: boolean;
  autoComplete?: string;
  maxLength?: number;
  minLength?: number;
  pattern?: string;
  id?: string;
  name?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  placeholder,
  value,
  onChange,
  onBlur,
  onFocus,
  type = 'text',
  disabled = false,
  required = false,
  error,
  success,
  helpText,
  className = '',
  size = 'md',
  variant = 'default',
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  autoFocus = false,
  autoComplete,
  maxLength,
  minLength,
  pattern,
  id,
  name,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-3 py-2 text-base',
    lg: 'px-4 py-3 text-lg'
  };

  const variantClasses = {
    default: 'border-gray-300 bg-white',
    filled: 'border-transparent bg-gray-100',
    outlined: 'border-2 border-gray-300 bg-transparent'
  };

  const baseClasses = clsx(
    'block w-full rounded-md shadow-sm transition-colors duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50',
    sizeClasses[size],
    variantClasses[variant],
    {
      'border-red-300 focus:border-red-500 focus:ring-red-500': error,
      'border-green-300 focus:border-green-500 focus:ring-green-500': success && !error,
      'border-gray-300 focus:border-blue-500 focus:ring-blue-500': !error && !success,
      'pl-10': LeftIcon,
      'pr-10': RightIcon || error || success
    },
    className
  );

  return (
    <div className="w-full">
      {label && (
        <label 
          htmlFor={inputId} 
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {LeftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <LeftIcon className="h-5 w-5 text-gray-400" />
          </div>
        )}
        
        <HeadlessInput
          ref={ref}
          id={inputId}
          name={name}
          type={type}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          onBlur={onBlur}
          onFocus={onFocus}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          autoFocus={autoFocus}
          autoComplete={autoComplete}
          maxLength={maxLength}
          minLength={minLength}
          pattern={pattern}
          className={baseClasses}
          {...props}
        />
        
        {(RightIcon || error || success) && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            {error && (
              <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
            )}
            {success && !error && (
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
            )}
            {RightIcon && !error && !success && (
              <RightIcon className="h-5 w-5 text-gray-400" />
            )}
          </div>
        )}
      </div>
      
      {(error || success || helpText) && (
        <div className="mt-1">
          {error && (
            <p className="text-sm text-red-600 flex items-center">
              <ExclamationCircleIcon className="h-4 w-4 mr-1" />
              {error}
            </p>
          )}
          {success && !error && (
            <p className="text-sm text-green-600 flex items-center">
              <CheckCircleIcon className="h-4 w-4 mr-1" />
              {success}
            </p>
          )}
          {helpText && !error && !success && (
            <p className="text-sm text-gray-500">{helpText}</p>
          )}
        </div>
      )}
    </div>
  );
});

Input.displayName = 'Input';