import React from 'react';
import { Card } from '../common/Card';

interface Activity {
  id: string;
  type: 'user' | 'exam' | 'grade' | 'system';
  title: string;
  description: string;
  timestamp: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface ActivityFeedCardProps {
  title: string;
  activities: Activity[];
  className?: string;
}

export const ActivityFeedCard: React.FC<ActivityFeedCardProps> = ({
  title,
  activities,
  className = ''
}) => {
  const getActivityColor = (type: Activity['type']) => {
    switch (type) {
      case 'user':
        return 'bg-blue-100 text-blue-600';
      case 'exam':
        return 'bg-green-100 text-green-600';
      case 'grade':
        return 'bg-purple-100 text-purple-600';
      case 'system':
        return 'bg-gray-100 text-gray-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <Card className={`p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-4">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-center justify-between py-2">
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${getActivityColor(activity.type)}`}>
                <activity.icon className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                <p className="text-xs text-gray-500">{activity.description}</p>
              </div>
            </div>
            <span className="text-xs text-gray-400">
              {new Date(activity.timestamp).toLocaleDateString()}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};