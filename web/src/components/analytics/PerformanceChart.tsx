import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Card } from '../common/Card';

interface ChartData {
  name: string;
  value: number;
  [key: string]: any;
}

interface PerformanceChartProps {
  title: string;
  data: ChartData[];
  type?: 'line' | 'bar';
  color?: string;
  className?: string;
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  title,
  data,
  type = 'line',
  color = '#3b82f6',
  className = ''
}) => {
  return (
    <Card className={`p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          {type === 'line' ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke={color} 
                strokeWidth={2}
                dot={{ fill: color, strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill={color} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </Card>
  );
};