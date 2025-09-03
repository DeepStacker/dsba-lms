import React, { useState } from 'react';
import { MagnifyingGlassIcon, FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { Button } from './Button';
import { Select } from './Select';

interface FilterOption {
  key: string;
  label: string;
  type: 'text' | 'select' | 'range' | 'date';
  options?: { value: string; label: string }[];
  placeholder?: string;
}

interface Filter {
  key: string;
  operator: 'equals' | 'contains' | 'greater' | 'less' | 'between';
  value: string | Date | [string, string];
}

interface SearchFilterProps {
  onFilter: (filters: Filter[]) => void;
  onSearch: (query: string) => void;
  filterOptions: FilterOption[];
  className?: string;
  placeholder?: string;
  withFilters?: boolean;
}

export const SearchFilter: React.FC<SearchFilterProps> = ({
  onFilter,
  onSearch,
  filterOptions,
  className = '',
  placeholder = 'Search...',
  withFilters = true,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Filter[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = () => {
    onSearch(searchQuery);
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const addFilter = () => {
    const nextOption = filterOptions.find(
      option => !filters.some(filter => filter.key === option.key)
    );

    if (nextOption) {
      setFilters(prev => [
        ...prev,
        {
          key: nextOption.key,
          operator: 'equals',
          value: '',
        },
      ]);
    }
  };

  const updateFilter = (index: number, updates: Partial<Filter>) => {
    setFilters(prev => {
      const newFilters = [...prev];
      newFilters[index] = { ...newFilters[index], ...updates };
      return newFilters;
    });
  };

  const removeFilter = (index: number) => {
    setFilters(prev => prev.filter((_, i) => i !== index));
  };

  const clearFilters = () => {
    setFilters([]);
    setSearchQuery('');
    onSearch('');
    onFilter([]);
  };

  const applyFilters = () => {
    onFilter(filters.filter(f => f.value !== ''));
  };

  const getFilterValueInput = (filter: Filter, index: number) => {
    const option = filterOptions.find(opt => opt.key === filter.key);
    if (!option) return null;

    switch (option.type) {
      case 'select':
        return (
          <Select
            options={option.options || []}
            value={String(filter.value)}
            onChange={(value) => updateFilter(index, { value: String(value || '') })}
            placeholder={option.placeholder}
            className="min-w-40"
          />
        );

      case 'date':
        // For now, using text input for date - can be enhanced with DatePicker
        return (
          <input
            type="date"
            value={String(filter.value)}
            onChange={(e) => updateFilter(index, { value: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 min-w-40"
            placeholder={option.placeholder}
          />
        );

      case 'range':
        return (
          <div className="flex gap-2 min-w-40">
            <input
              type="number"
              placeholder="Min"
              value={Array.isArray(filter.value) ? filter.value[0] : ''}
              onChange={(e) => {
                const currentValue = Array.isArray(filter.value) ? filter.value : ['', ''];
                updateFilter(index, { value: [e.target.value, currentValue[1]] });
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 w-20"
            />
            <input
              type="number"
              placeholder="Max"
              value={Array.isArray(filter.value) ? filter.value[1] : ''}
              onChange={(e) => {
                const currentValue = Array.isArray(filter.value) ? filter.value : ['', ''];
                updateFilter(index, { value: [currentValue[0], e.target.value] });
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 w-20"
            />
          </div>
        );

      case 'text':
      default:
        return (
          <input
            type="text"
            value={String(filter.value)}
            onChange={(e) => updateFilter(index, { value: e.target.value })}
            placeholder={option.placeholder}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 min-w-40"
          />
        );
    }
  };

  const getOperatorOptions = (filter: Filter) => {
    const option = filterOptions.find(opt => opt.key === filter.key);
    if (!option) return [{ value: 'equals', label: 'Equals' }];

    switch (option.type) {
      case 'text':
        return [
          { value: 'equals', label: 'Equals' },
          { value: 'contains', label: 'Contains' },
        ];
      case 'range':
      case 'date':
        return [
          { value: 'equals', label: 'Equals' },
          { value: 'greater', label: 'Greater than' },
          { value: 'less', label: 'Less than' },
          { value: 'between', label: 'Between' },
        ];
      case 'select':
      default:
        return [{ value: 'equals', label: 'Equals' }];
    }
  };

  const availableOptions = filterOptions.filter(
    option => !filters.some(filter => filter.key === option.key)
  );

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Search Bar */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder={placeholder}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleSearchKeyPress}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
          <Button onClick={handleSearch} variant="primary" className="px-6">
            Search
          </Button>
          {withFilters && (
            <Button
              variant="secondary"
              onClick={() => setShowFilters(!showFilters)}
              className="px-4"
            >
              <FunnelIcon className="h-5 w-5" />
              Filters
            </Button>
          )}
          {(searchQuery || filters.length > 0) && (
            <Button variant="danger" onClick={clearFilters}>
              <XMarkIcon className="h-4 w-4" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="space-y-3">
            {filters.map((filter, index) => {
              const option = filterOptions.find(opt => opt.key === filter.key);
              const operators = getOperatorOptions(filter);

              return (
                <div key={index} className="flex items-center gap-3 bg-white p-3 rounded-md border">
                  <span className="text-sm font-medium min-w-24">{option?.label}:</span>

                  <Select
                    options={operators}
                    value={filter.operator}
                    onChange={(value) => updateFilter(index, { operator: value as Filter['operator'] })}
                    className="min-w-28"
                  />

                  {getFilterValueInput(filter, index)}

                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => removeFilter(index)}
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </Button>
                </div>
              );
            })}

            <div className="flex items-center justify-between">
              {availableOptions.length > 0 && (
                <Button variant="secondary" size="sm" onClick={addFilter}>
                  Add Filter
                </Button>
              )}
              {filters.length > 0 && (
                <div className="flex gap-2">
                  <Button variant="success" size="sm" onClick={applyFilters}>
                    Apply Filters
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Active Filters Summary */}
      {(searchQuery || filters.filter(f => f.value !== '').length > 0) && (
        <div className="p-3 bg-blue-50 border-b border-blue-100">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-blue-900">Active:</span>

            {searchQuery && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Search: "{searchQuery}"
              </span>
            )}

            {filters.filter(f => f.value !== '').map((filter, index) => {
              const option = filterOptions.find(opt => opt.key === filter.key);
              const operator = getOperatorOptions(filter).find(o => o.value === filter.operator);

              return (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                >
                  {option?.label} {operator?.label?.toLowerCase()} {String(filter.value)}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
