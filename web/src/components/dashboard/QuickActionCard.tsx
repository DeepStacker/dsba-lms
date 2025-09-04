import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  badge?: string | number;
}

interface QuickActionCardProps {
  title: string;
  actions: QuickAction[];
  className?: string;
}

export const QuickActionCard: React.FC<QuickActionCardProps> = ({
  title,
  actions,
  className = ''
}) => {
  return (
    <Card className={`p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-3">
        {actions.map((action) => (
          <Button
            key={action.id}
            variant={action.variant || 'secondary'}
            size="lg"
            onClick={action.onClick}
            className="w-full justify-between"
          >
            <span className="flex items-center">
              <action.icon className="h-5 w-5 mr-3" />
              {action.label}
            </span>
            {action.badge && (
              <span className="text-sm">{action.badge}</span>
            )}
          </Button>
        ))}
      </div>
    </Card>
  );
};