import React, { forwardRef } from 'react';
import { ChevronDownIcon, CheckIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { Listbox } from '@headlessui/react';

interface Option {
  value: string | number;
  label: string;
  disabled?: boolean;
}

interface SelectProps {
  label?: string;
  options: Option[];
  placeholder?: string;
  value?: string | number | null;
  onChange: (value: string | number | null) => void;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  className?: string;
  multiple?: boolean;
  searchable?: boolean;
}

export const Select: React.FC<SelectProps> = ({
  label,
  options,
  placeholder = "Select an option",
  value,
  onChange,
  error,
  helperText,
  disabled = false,
  className = '',
  multiple = false,
  searchable = false,
}) => {
  const selectedOption = options.find(option => option.value === value);
  const selectedOptions = multiple && Array.isArray(value)
    ? options.filter(option => value.includes(option.value))
    : [];

  return (
    <div className={`space-y-1 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}

      <div className="relative">
        <Listbox value={value} onChange={onChange} disabled={disabled}>
          <div className="relative">
            <Listbox.Button
              className={`relative w-full rounded-md border bg-white pl-3 pr-10 py-2 text-left shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 cursor-pointer ${
                error
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300'
              } ${disabled ? 'bg-gray-50 cursor-not-allowed' : ''}`}
            >
              <span className="block truncate">
                {multiple
                  ? selectedOptions.length > 0
                    ? `${selectedOptions.length} selected`
                    : placeholder
                  : selectedOption?.label || placeholder
                }
              </span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronDownIcon
                  className="h-5 w-5 text-gray-400"
                  aria-hidden="true"
                />
              </span>
              {error && (
                <span className="pointer-events-none absolute inset-y-0 right-6 flex items-center">
                  <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                </span>
              )}
            </Listbox.Button>

            <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
              {options.map((option) => (
                <Listbox.Option
                  key={option.value}
                  className={({ active, disabled }) =>
                    `relative cursor-pointer select-none py-2 pl-8 pr-4 ${
                      active ? 'bg-blue-100 text-blue-900' : 'text-gray-900'
                    } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`
                  }
                  value={option}
                  disabled={option.disabled}
                >
                  {({ selected }) => (
                    <>
                      <span
                        className={`block truncate ${
                          selected ? 'font-medium' : 'font-normal'
                        }`}
                      >
                        {option.label}
                      </span>
                      {selected ? (
                        <span className="absolute inset-y-0 left-0 flex items-center pl-1.5">
                          <CheckIcon className="h-5 w-5" aria-hidden="true" />
                        </span>
                      ) : null}
                    </>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </div>
        </Listbox>
      </div>

      {(error || helperText) && (
        <p className={`text-sm ${error ? 'text-red-600' : 'text-gray-500'}`}>
          {error || helperText}
        </p>
      )}
    </div>
  );
};
