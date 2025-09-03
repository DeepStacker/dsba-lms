import React, { useState } from 'react';
import { CalendarIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { Popover } from '@headlessui/react';
import { format, isToday, isTomorrow, isYesterday } from 'date-fns';

interface DatePickerProps {
  label?: string;
  value?: Date | null;
  onChange: (date: Date | null) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  helperText?: string;
  className?: string;
  minDate?: Date;
  maxDate?: Date;
}

export const DatePicker: React.FC<DatePickerProps> = ({
  label,
  value,
  onChange,
  placeholder = "Select a date",
  disabled = false,
  error,
  helperText,
  className = '',
  minDate,
  maxDate,
}) => {
    const [, setIsOpen] = useState(false); // eslint-disable-line no-unused-vars

  const formatDateForDisplay = (date: Date) => {
    if (isToday(date)) return 'Today';
    if (isTomorrow(date)) return 'Tomorrow';
    if (isYesterday(date)) return 'Yesterday';
    return format(date, 'PPP');
  };

  const getDaysInMonth = (month: number, year: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const [currentDate, setCurrentDate] = useState(value || new Date());

  const goToPreviousMonth = () => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  };

  const selectDate = (date: Date) => {
    onChange(date);
    setIsOpen(false);
  };

  const month = currentDate.getMonth();
  const year = currentDate.getFullYear();
  const daysInMonth = getDaysInMonth(month, year);
  const firstDayOfMonth = new Date(year, month, 1).getDay();

  const isDateDisabled = (date: Date) => {
    if (minDate && date < minDate) return true;
    if (maxDate && date > maxDate) return true;
    return false;
  };

  const getDayClass = (day: number) => {
    const date = new Date(year, month, day);
    const isSelected = value && format(value, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd');
    const isInPast = date < new Date() && !isToday(date);
    const disabled = isDateDisabled(date);

    let classes = 'relative py-1.5 px-2 w-8 h-8 text-center text-sm hover:bg-gray-100 rounded-full cursor-pointer ';

    if (isSelected) {
      classes += 'bg-blue-600 text-white hover:bg-blue-700';
    } else if (disabled) {
      classes += 'text-gray-300 cursor-not-allowed hover:bg-transparent';
    } else if (isInPast && !minDate) {
      classes += 'text-gray-500 hover:bg-gray-50';
    } else {
      classes += 'text-gray-900 hover:bg-gray-100';
    }

    return classes;
  };

  return (
    <div className={`space-y-1 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}

      <Popover className="relative">
        <Popover.Button
          disabled={disabled}
          className={`w-full text-left px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            error
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300'
          } ${disabled ? 'bg-gray-50 cursor-not-allowed' : ''} flex items-center justify-between`}
        >
          <span className={value ? 'text-gray-900' : 'text-gray-500'}>
            {value ? formatDateForDisplay(value) : placeholder}
          </span>
          <CalendarIcon className="h-5 w-5 text-gray-400 ml-2" />

          {error && (
            <div className="absolute inset-y-0 right-9 flex items-center">
              <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
            </div>
          )}
        </Popover.Button>

        <Popover.Panel className="absolute z-10 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg">
          <div className="p-4">
            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-4">
              <button
                type="button"
                onClick={goToPreviousMonth}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <span className="text-sm">‹</span>
              </button>
              <span className="text-sm font-medium">
                {format(currentDate, 'MMMM yyyy')}
              </span>
              <button
                type="button"
                onClick={goToNextMonth}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <span className="text-sm">›</span>
              </button>
            </div>

            {/* Days of the Week */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
                <div key={day} className="text-center text-xs font-medium text-gray-500 py-1">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7 gap-1">
              {/* Empty cells for days before the first day of the month */}
              {Array.from({ length: firstDayOfMonth }).map((_, index) => (
                <div key={`empty-${index}`} className="py-1.5 px-2"></div>
              ))}

              {/* Days of the month */}
              {Array.from({ length: daysInMonth }, (_, i) => i + 1).map(day => {
                const date = new Date(year, month, day);
                return (
                  <button
                    key={day}
                    type="button"
                    className={getDayClass(day)}
                    onClick={() => !isDateDisabled(date) && selectDate(date)}
                    disabled={isDateDisabled(date)}
                  >
                    {day}
                  </button>
                );
              })}
            </div>
          </div>
        </Popover.Panel>
      </Popover>

      {(error || helperText) && (
        <p className={`text-sm ${error ? 'text-red-600' : 'text-gray-500'}`}>
          {error || helperText}
        </p>
      )}
    </div>
  );
};
