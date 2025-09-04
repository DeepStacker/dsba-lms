import React from 'react';
import { Card } from '../common/Card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SemesterGrade {
  semester: number;
  sgpa: number;
  courses: number;
}

interface SGPACGPACardProps {
  currentSGPA: number;
  currentCGPA: number;
  semesterGrades: SemesterGrade[];
  className?: string;
}

export const SGPACGPACard: React.FC<SGPACGPACardProps> = ({
  currentSGPA,
  currentCGPA,
  semesterGrades,
  className = ''
}) => {
  return (
    <Card className={`p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Academic Performance</h3>
      
      {/* Current SGPA/CGPA */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-blue-600">{currentSGPA.toFixed(2)}</div>
          <div className="text-sm text-gray-600">Current SGPA</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-green-600">{currentCGPA.toFixed(2)}</div>
          <div className="text-sm text-gray-600">Overall CGPA</div>
        </div>
      </div>

      {/* SGPA Trend Chart */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">SGPA Trend</h4>
        <div className="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={semesterGrades}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="semester" 
                tickFormatter={(value) => `Sem ${value}`}
              />
              <YAxis domain={[0, 10]} />
              <Tooltip 
                formatter={(value: number) => [value.toFixed(2), 'SGPA']}
                labelFormatter={(label) => `Semester ${label}`}
              />
              <Line 
                type="monotone" 
                dataKey="sgpa" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Semester Details */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700">Semester Details</h4>
        {semesterGrades.map((grade) => (
          <div key={grade.semester} className="flex justify-between items-center py-1">
            <span className="text-sm text-gray-600">Semester {grade.semester}</span>
            <div className="text-right">
              <span className="text-sm font-medium text-gray-900">
                {grade.sgpa.toFixed(2)}
              </span>
              <span className="text-xs text-gray-500 ml-2">
                ({grade.courses} courses)
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};