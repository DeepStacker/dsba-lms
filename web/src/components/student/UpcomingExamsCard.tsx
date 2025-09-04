import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

interface UpcomingExam {
  id: string;
  title: string;
  course: string;
  startTime: string;
  duration: number;
  totalMarks: number;
  canJoin: boolean;
}

interface UpcomingExamsCardProps {
  exams: UpcomingExam[];
  onJoinExam: (examId: string) => void;
  className?: string;
}

export const UpcomingExamsCard: React.FC<UpcomingExamsCardProps> = ({
  exams,
  onJoinExam,
  className = ''
}) => {
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  };

  const getTimeUntilExam = (startTime: string) => {
    const now = new Date();
    const examTime = new Date(startTime);
    const diffMs = examTime.getTime() - now.getTime();
    
    if (diffMs < 0) return 'Started';
    
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 24) {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays} day${diffDays > 1 ? 's' : ''}`;
    } else if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes}m`;
    } else {
      return `${diffMinutes}m`;
    }
  };

  return (
    <Card className={`p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Exams</h3>
      
      <div className="space-y-4">
        {exams.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No upcoming exams</p>
          </div>
        ) : (
          exams.map((exam) => {
            const { date, time } = formatDateTime(exam.startTime);
            const timeUntil = getTimeUntilExam(exam.startTime);
            
            return (
              <div key={exam.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-medium text-gray-900">{exam.title}</h4>
                    <p className="text-sm text-gray-600">{exam.course}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-blue-600">
                      {timeUntil}
                    </div>
                    <div className="text-xs text-gray-500">remaining</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                  <div>
                    <span className="text-gray-500">Date:</span>
                    <div className="font-medium">{date}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Time:</span>
                    <div className="font-medium">{time}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Duration:</span>
                    <div className="font-medium">{exam.duration} min</div>
                  </div>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">
                    Total Marks: {exam.totalMarks}
                  </span>
                  <Button
                    variant={exam.canJoin ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => onJoinExam(exam.id)}
                    disabled={!exam.canJoin}
                  >
                    {exam.canJoin ? 'Join Exam' : 'Not Available'}
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
};