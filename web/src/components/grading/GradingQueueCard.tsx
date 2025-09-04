import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

interface GradingItem {
  id: string;
  examTitle: string;
  studentName: string;
  questionText: string;
  submittedAt: string;
  aiScore?: number;
  maxMarks: number;
}

interface GradingQueueCardProps {
  title: string;
  items: GradingItem[];
  onGradeItem: (itemId: string) => void;
  onBulkAIGrade: () => void;
  className?: string;
}

export const GradingQueueCard: React.FC<GradingQueueCardProps> = ({
  title,
  items,
  onGradeItem,
  onBulkAIGrade,
  className = ''
}) => {
  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <Button variant="primary" size="sm" onClick={onBulkAIGrade}>
          Bulk AI Grade
        </Button>
      </div>

      <div className="space-y-4">
        {items.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No items pending grading</p>
          </div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{item.examTitle}</h4>
                  <p className="text-sm text-gray-600">Student: {item.studentName}</p>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                    {item.questionText}
                  </p>
                </div>
                <div className="ml-4 text-right">
                  {item.aiScore !== undefined ? (
                    <div className="text-sm">
                      <span className="text-blue-600 font-medium">AI: {item.aiScore}</span>
                      <span className="text-gray-500">/{item.maxMarks}</span>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">
                      Max: {item.maxMarks}
                    </div>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(item.submittedAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex justify-end">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onGradeItem(item.id)}
                >
                  Grade Now
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};