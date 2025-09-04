import React from 'react';
import { Card } from '../common/Card';
import { UserGroupIcon, CogIcon } from '@heroicons/react/24/outline';

interface HealthStatus {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  icon?: React.ComponentType<{ className?: string }>;
  value?: string | number;
}

interface SystemHealthCardProps {
  title: string;
  healthItems: HealthStatus[];
  className?: string;
}

export const SystemHealthCard: React.FC<SystemHealthCardProps> = ({
  title,
  healthItems,
  className = ''
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'border-green-200 bg-green-50 text-green-600';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 text-yellow-600';
      case 'error':
        return 'border-red-200 bg-red-50 text-red-600';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-600';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'warning':
        return 'Warning';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const getStatusDot = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <Card className={`p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-4">
        {healthItems.map((item, index) => (
          <div
            key={index}
            className={`flex items-center justify-between p-3 border rounded-lg ${getStatusColor(item.status)}`}
          >
            <span className="flex items-center">
              {item.icon ? (
                <item.icon className="h-4 w-4 mr-3" />
              ) : (
                <div className={`w-2 h-2 rounded-full mr-3 ${getStatusDot(item.status)}`}></div>
              )}
              <span className="text-sm font-medium">{item.name}</span>
            </span>
            <span className="text-sm font-semibold">
              {item.value || getStatusText(item.status)}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};