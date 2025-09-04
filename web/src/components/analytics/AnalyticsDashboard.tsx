import React, { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Select } from '../common/Select';
import { 
  ChartBarIcon, 
  DocumentArrowDownIcon,
  AcademicCapIcon,
  UserGroupIcon 
} from '@heroicons/react/24/outline';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  PieChart, 
  Pie, 
  Cell, 
  LineChart, 
  Line,
  ResponsiveContainer 
} from 'recharts';
import { analyticsApi } from '../../utils/api';
import toast from 'react-hot-toast';

interface AnalyticsData {
  coAttainment: Array<{
    co_code: string;
    co_title: string;
    attainment_percentage: number;
    student_count: number;
    avg_score: number;
  }>;
  gradeDistribution: Array<{
    grade: string;
    count: number;
    percentage: number;
  }>;
  performanceTrends: Array<{
    month: string;
    average: number;
    students: number;
  }>;
  systemStats: {
    totalUsers: number;
    activeExams: number;
    totalQuestions: number;
    completionRate: number;
  };
}

export const AnalyticsDashboard: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('current_semester');
  const [selectedProgram, setSelectedProgram] = useState('all');

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  useEffect(() => {
    fetchAnalytics();
  }, [selectedPeriod, selectedProgram]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration
      const mockData: AnalyticsData = {
        coAttainment: [
          { co_code: 'CO1', co_title: 'Programming Fundamentals', attainment_percentage: 85.5, student_count: 32, avg_score: 8.2 },
          { co_code: 'CO2', co_title: 'OOP Concepts', attainment_percentage: 78.3, student_count: 32, avg_score: 7.8 },
          { co_code: 'CO3', co_title: 'Data Structures', attainment_percentage: 82.1, student_count: 32, avg_score: 8.0 },
          { co_code: 'CO4', co_title: 'Algorithm Analysis', attainment_percentage: 76.8, student_count: 32, avg_score: 7.5 },
          { co_code: 'CO5', co_title: 'Problem Solving', attainment_percentage: 88.2, student_count: 32, avg_score: 8.5 }
        ],
        gradeDistribution: [
          { grade: 'O', count: 8, percentage: 25 },
          { grade: 'A+', count: 10, percentage: 31.25 },
          { grade: 'A', count: 7, percentage: 21.88 },
          { grade: 'B+', count: 4, percentage: 12.5 },
          { grade: 'B', count: 2, percentage: 6.25 },
          { grade: 'C', count: 1, percentage: 3.12 }
        ],
        performanceTrends: [
          { month: 'Jan', average: 7.2, students: 30 },
          { month: 'Feb', average: 7.5, students: 31 },
          { month: 'Mar', average: 7.8, students: 32 },
          { month: 'Apr', average: 8.1, students: 32 },
          { month: 'May', average: 8.3, students: 32 },
          { month: 'Jun', average: 8.0, students: 31 }
        ],
        systemStats: {
          totalUsers: 1247,
          activeExams: 8,
          totalQuestions: 2156,
          completionRate: 94.5
        }
      };
      
      setAnalyticsData(mockData);
    } catch (error) {
      toast.error('Failed to fetch analytics data');
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = (format: string) => {
    toast.success(`Exporting report as ${format.toUpperCase()}...`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Comprehensive performance analytics and reports</p>
        </div>
        <div className="flex gap-3">
          <Select
            value={selectedPeriod}
            onChange={setSelectedPeriod}
            options={[
              { value: 'current_semester', label: 'Current Semester' },
              { value: 'last_semester', label: 'Last Semester' },
              { value: 'academic_year', label: 'Academic Year' }
            ]}
          />
          <Button
            variant="secondary"
            onClick={() => handleExportReport('pdf')}
            className="flex items-center gap-2"
          >
            <DocumentArrowDownIcon className="h-5 w-5" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <UserGroupIcon className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">{analyticsData.systemStats.totalUsers}</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Exams</p>
              <p className="text-2xl font-bold text-gray-900">{analyticsData.systemStats.activeExams}</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center">
            <AcademicCapIcon className="h-8 w-8 text-purple-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Questions</p>
              <p className="text-2xl font-bold text-gray-900">{analyticsData.systemStats.totalQuestions}</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-orange-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Completion Rate</p>
              <p className="text-2xl font-bold text-gray-900">{analyticsData.systemStats.completionRate}%</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CO Attainment Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">CO Attainment Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.coAttainment}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="co_code" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="attainment_percentage" fill="#3B82F6" name="Attainment %" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Grade Distribution Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Grade Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analyticsData.gradeDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ grade, percentage }) => `${grade} (${percentage}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {analyticsData.gradeDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Performance Trends */}
        <Card className="p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData.performanceTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="average" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Average Score"
              />
              <Line 
                type="monotone" 
                dataKey="students" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Student Count"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Detailed CO Attainment Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed CO Attainment</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  CO Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Course Outcome
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Attainment %
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Students
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analyticsData.coAttainment.map((co, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {co.co_code}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {co.co_title}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${co.attainment_percentage}%` }}
                        ></div>
                      </div>
                      {co.attainment_percentage}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {co.avg_score}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {co.student_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      co.attainment_percentage >= 80 
                        ? 'bg-green-100 text-green-800' 
                        : co.attainment_percentage >= 60 
                        ? 'bg-yellow-100 text-yellow-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {co.attainment_percentage >= 80 ? 'Excellent' : 
                       co.attainment_percentage >= 60 ? 'Good' : 'Needs Improvement'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};