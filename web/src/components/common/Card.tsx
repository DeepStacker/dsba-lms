import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

interface CardHeaderProps {
  title?: string;
  subtitle?: string;
  children?: React.ReactNode;
}

interface CardContentProps {
  children: React.ReactNode;
}

interface CardFooterProps {
  children: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  className = '',
  padding = 'md',
}) => {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  return (
    <div className={`bg-white shadow-sm border border-gray-200 rounded-lg ${className}`}>
      {title && (
        <div className={`border-b border-gray-200 ${paddingStyles[padding] || 'p-6'}`}>
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
      )}
      <div className={paddingStyles[padding]}>
        {children}
      </div>
    </div>
  );
};

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  children
}) => (
  <div className="px-6 py-4 border-b border-gray-200">
    {title && <h3 className="text-lg font-medium text-gray-900">{title}</h3>}
    {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
    {children}
  </div>
);

export const CardContent: React.FC<CardContentProps> = ({ children }) => (
  <div className="px-6 py-4">{children}</div>
);

export const CardFooter: React.FC<CardFooterProps> = ({ children }) => (
  <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">{children}</div>
);