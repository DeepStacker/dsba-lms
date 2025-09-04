import React from 'react';
import { Card } from '../common/Card';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  onClick?: () => void;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  change,
  changeType = 'neutral',
  onClick,
  className = ''
}) => {
  const getChangeColor = () => {
    switch (changeType) {
      case 'increase':
        return 'text-green-600';
      case 'decrease':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getChangeIcon = () => {
    switch (changeType) {
      case 'increase':
        return <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />;
      case 'decrease':
        return <ArrowDownIcon className="h-4 w-4 text-red-500 mr-1" />;
      default:
        return null;
    }
  };

  return (
    <Card 
      className={`p-6 hover:shadow-lg transition-shadow ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {change && (
            <div className="flex items-center mt-2">
              {getChangeIcon()}
              <span className={`text-xs font-medium ${getChangeColor()}`}>
                {change}
              </span>
            </div>
          )}
        </div>
        <Icon className="h-12 w-12 text-blue-100" />
      </div>
    </Card>
  );
};