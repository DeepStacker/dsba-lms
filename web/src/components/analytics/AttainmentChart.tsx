import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../common/Card';

interface AttainmentData {
  code: string;
  title: string;
  attainment: number;
}

interface AttainmentChartProps {
  title: string;
  data: AttainmentData[];
  type: 'CO' | 'PO';
  className?: string;
}

export const AttainmentChart: React.FC<AttainmentChartProps> = ({
  title,
  data,
  type,
  className = ''
}) => {
  const getBarColor = (attainment: number) => {
    if (attainment >= 80) return '#22c55e'; // Green
    if (attainment >= 60) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const formatTooltip = (value: number, name: string, props: any) => {
    return [`${value.toFixed(1)}%`, `${type} Attainment`];
  };

  return (
    <Card className={`p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="code" />
            <YAxis domain={[0, 100]} />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={(label) => {
                const item = data.find(d => d.code === label);
                return item ? `${item.code}: ${item.title}` : label;
              }}
            />
            <Bar dataKey="attainment" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.attainment)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      {/* Legend */}
      <div className="flex justify-center mt-4 space-x-6">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
          <span className="text-sm text-gray-600">≥80% (Excellent)</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-yellow-500 rounded mr-2"></div>
          <span className="text-sm text-gray-600">60-79% (Good)</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-red-500 rounded mr-2"></div>
          <span className="text-sm text-gray-600">&lt;60% (Needs Improvement)</span>
        </div>
      </div>
    </Card>
  );
};