import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

interface ExamStats {
  totalStudents: number;
  joined: number;
  active: number;
  submitted: number;
  flagged: number;
}

interface ExamMonitorCardProps {
  examTitle: string;
  stats: ExamStats;
  timeRemaining: string;
  status: 'upcoming' | 'active' | 'ended';
  onStartExam?: () => void;
  onEndExam?: () => void;
  onViewDetails?: () => void;
  className?: string;
}

export const ExamMonitorCard: React.FC<ExamMonitorCardProps> = ({
  examTitle,
  stats,
  timeRemaining,
  status,
  onStartExam,
  onEndExam,
  onViewDetails,
  className = ''
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'upcoming':
        return 'bg-blue-100 text-blue-800';
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'ended':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'upcoming':
        return 'Upcoming';
      case 'active':
        return 'Active';
      case 'ended':
        return 'Ended';
      default:
        return 'Unknown';
    }
  };

  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{examTitle}</h3>
          <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full mt-1 ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">Time Remaining</p>
          <p className="text-lg font-bold text-gray-900">{timeRemaining}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{stats.totalStudents}</p>
          <p className="text-sm text-gray-600">Total</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600">{stats.joined}</p>
          <p className="text-sm text-gray-600">Joined</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">{stats.active}</p>
          <p className="text-sm text-gray-600">Active</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-purple-600">{stats.submitted}</p>
          <p className="text-sm text-gray-600">Submitted</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-red-600">{stats.flagged}</p>
          <p className="text-sm text-gray-600">Flagged</p>
        </div>
      </div>

      <div className="flex gap-3">
        {status === 'upcoming' && onStartExam && (
          <Button variant="primary" onClick={onStartExam}>
            Start Exam
          </Button>
        )}
        {status === 'active' && onEndExam && (
          <Button variant="warning" onClick={onEndExam}>
            End Exam
          </Button>
        )}
        <Button variant="secondary" onClick={onViewDetails}>
          View Details
        </Button>
      </div>
    </Card>
  );
};