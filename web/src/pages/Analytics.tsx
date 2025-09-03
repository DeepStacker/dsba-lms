import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Select } from '../components/common/Select';
import { analyticsApi, examsApi, gradingApi } from '../utils/api';
import {
  ChartBarIcon,
  AcademicCapIcon,
  BookOpenIcon,
  UserGroupIcon,
  DocumentCheckIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  Bars3Icon,
  UserCircleIcon,
  CogIcon,
  ChartPieIcon,
  PresentationChartLineIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import { DataTable } from '../components/common/DataTable';
import toast from 'react-hot-toast';

interface AnalyticData {
  totalStudents: number;
  totalExams: number;
  totalQuestions: number;
  totalPrograms: number;
  avgGrade: number;
  passRate: number;
  coAttainment: {
    knowledge: number;
    comprehension: number;
    application: number;
    analysis: number;
    evaluation: number;
    synthesis: number;
  };
  performanceTrends: Array<{
    period: string;
    avgGrade: number;
    passRate: number;
  }>;
  subjectPerformance: Array<{
    subject: string;
    avgGrade: number;
    passRate: number;
    studentCount: number;
  }>;
  examAnalytics: Array<{
    examTitle: string;
    totalAttempts: number;
    avgScore: number;
    completionRate: number;
    difficulty: number;
  }>;
}

const Analytics: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<AnalyticData | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('semester');
  const [selectedView, setSelectedView] = useState<'overview' | 'performance' | 'co-po' | 'reports'>('overview');
  const [filterByDate, setFilterByDate] = useState({ startDate: '', endDate: '' });

  useEffect(() => {
    fetchAnalyticsData();
  }, [selectedPeriod]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      // In a real implementation, this would call actual analytics APIs
      const mockAnalytics: AnalyticData = {
        totalStudents: 1245,
        totalExams: 89,
        totalQuestions: 2340,
        totalPrograms: 12,
        avgGrade: 78.5,
        passRate: 85.2,
        coAttainment: {
          knowledge: 85,
          comprehension: 82,
          application: 79,
          analysis: 76,
          evaluation: 74,
          synthesis: 72
        },
        performanceTrends: [
          { period: 'Jan', avgGrade: 76, passRate: 83 },
          { period: 'Feb', avgGrade: 78, passRate: 84 },
          { period: 'Mar', avgGrade: 80, passRate: 86 },
          { period: 'Apr', avgGrade: 79, passRate: 87 },
          { period: 'May', avgGrade: 81, passRate: 88 },
          { period: 'Jun', avgGrade: 78, passRate: 85 }
        ],
        subjectPerformance: [
          { subject: 'Mathematics', avgGrade: 82, passRate: 88, studentCount: 320 },
          { subject: 'Computer Science', avgGrade: 85, passRate: 92, studentCount: 280 },
          { subject: 'Physics', avgGrade: 76, passRate: 81, studentCount: 240 },
          { subject: 'Chemistry', avgGrade: 79, passRate: 84, studentCount: 220 },
          { subject: 'Electronics', avgGrade: 74, passRate: 78, studentCount: 185 }
        ],
        examAnalytics: [
          { examTitle: 'Data Structures Final', totalAttempts: 145, avgScore: 78, completionRate: 92, difficulty: 3 },
          { examTitle: 'Mathematics Mid-term', totalAttempts: 223, avgScore: 82, completionRate: 95, difficulty: 2 },
          { examTitle: 'Database Systems', totalAttempts: 156, avgScore: 75, completionRate: 88, difficulty: 3 },
          { examTitle: 'Web Development', totalAttempts: 98, avgScore: 79, completionRate: 91, difficulty: 2 }
        ]
      };

      // Simulate API call delay
      setTimeout(() => {
        setAnalyticsData(mockAnalytics);
        setLoading(false);
      }, 1000);

    } catch (error) {
      toast.error('Failed to fetch analytics data');
      setLoading(false);
    }
  };

  const exportAnalytics = async (format: 'pdf' | 'excel' | 'csv') => {
    try {
      toast.success(`Exporting analytics report as ${format.toUpperCase()}...`);
      // In real implementation, this would call an export API
    } catch (error) {
      toast.error('Failed to export analytics report');
    }
  };

  const generateCOAttainment = async (examId?: number) => {
    try {
      const response = await analyticsApi.getAnalytics('co-attainment', examId);
      toast.success('CO attainment analysis generated successfully!');
    } catch (error) {
      toast.error('Failed to generate CO attainment report');
    }
  };

  const generatePOAttainment = async (examId?: number) => {
    try {
      const response = await analyticsApi.getAnalytics('po-attainment', examId);
      toast.success('PO attainment analysis generated successfully!');
    } catch (error) {
      toast.error('Failed to generate PO attainment report');
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics & Reports</h1>
          <p className="text-gray-600 mt-1">Comprehensive analysis and insights for academic excellence</p>
        </div>
        <div className="flex gap-3">
          <Select
            options={[
              { value: 'semester', label: 'This Semester' },
              { value: 'academic_year', label: 'This Academic Year' },
              { value: 'custom', label: 'Custom Range' }
            ]}
            value={selectedPeriod}
            onChange={(value) => setSelectedPeriod(String(value || 'semester'))}
          />
          <Button
            variant="secondary"
            onClick={() => exportAnalytics('pdf')}
            className="flex items-center gap-2"
          >
            <DocumentCheckIcon className="h-5 w-5" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* View Selector */}
      <div className="flex gap-2 mb-6">
        {[
          { key: 'overview', label: 'Overview', icon: ChartBarIcon },
          { key: 'performance', label: 'Performance', icon: ArrowTrendingUpIcon },
          { key: 'co-po', label: 'CO/PO Analysis', icon: AcademicCapIcon },
          { key: 'reports', label: 'Reports', icon: PresentationChartLineIcon }
        ].map(({ key, label, icon: Icon }) => (
          <Button
            key={key}
            variant={selectedView === key ? 'primary' : 'secondary'}
            onClick={() => setSelectedView(key as any)}
            className="flex items-center gap-2"
          >
            <Icon className="h-4 w-4" />
            {label}
          </Button>
        ))}
      </div>

      {/* Overview Cards */}
      {selectedView === 'overview' && analyticsData && (
        <>
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{analyticsData.totalStudents}</p>
                  <p className="text-sm text-gray-600">Total Students</p>
                </div>
                <UserGroupIcon className="h-12 w-12 text-blue-500" />
              </div>
              <div className="mt-4 flex items-center">
                <ArrowUpIcon className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600 ml-1">12%</span>
                <span className="text-sm text-gray-600 ml-2">vs last period</span>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{analyticsData.totalExams}</p>
                  <p className="text-sm text-gray-600">Active Exams</p>
                </div>
                <DocumentCheckIcon className="h-12 w-12 text-green-500" />
              </div>
              <div className="mt-4 flex items-center">
                <ArrowUpIcon className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600 ml-1">8%</span>
                <span className="text-sm text-gray-600 ml-2">new this month</span>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{analyticsData.avgGrade.toFixed(1)}</p>
                  <p className="text-sm text-gray-600">Average Grade</p>
                </div>
                <ChartBarIcon className="h-12 w-12 text-purple-500" />
              </div>
              <div className="mt-4 flex items-center">
                <ArrowUpIcon className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600 ml-1">3.2%</span>
                <span className="text-sm text-gray-600 ml-2">from last semester</span>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900">{analyticsData.passRate.toFixed(1)}%</p>
                  <p className="text-sm text-gray-600">Pass Rate</p>
                </div>
                <ArrowTrendingUpIcon className="h-12 w-12 text-orange-500" />
              </div>
              <div className="mt-4 flex items-center">
                <ArrowUpIcon className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600 ml-1">5.1%</span>
                <span className="text-sm text-gray-600 ml-2">from last semester</span>
              </div>
            </Card>
          </div>

          {/* Quick Insights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Trends</h3>
              <div className="space-y-3">
                {analyticsData.performanceTrends.slice(-4).map((trend, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-2 h-8 bg-blue-500 rounded mr-3"></div>
                      <span className="text-sm font-medium">{trend.period}</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm font-semibold text-gray-900">{trend.avgGrade}%</span>
                      <span className="text-xs text-gray-500 ml-2">({trend.passRate}% pass)</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performing Subjects</h3>
              <div className="space-y-3">
                {analyticsData.subjectPerformance.slice(0, 4).map((subject, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className={`text-xs font-bold px-2 py-1 rounded ${
                        index === 0 ? 'bg-yellow-100 text-yellow-800' :
                        index === 1 ? 'bg-gray-100 text-gray-800' :
                        index === 2 ? 'bg-orange-100 text-orange-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        #{index + 1}
                      </span>
                      <span className="text-sm font-medium ml-3">{subject.subject}</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm font-semibold text-gray-900">{subject.avgGrade}%</span>
                      <span className="text-xs text-gray-500 ml-2">({subject.passRate}% pass)</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* CO Attainment Overview */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Course Outcome (CO) Attainment</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(analyticsData.coAttainment).map(([level, attainment], index) => (
                <div key={level} className="text-center">
                  <div className={`relative w-16 h-16 mx-auto mb-2 rounded-full flex items-center justify-center ${
                    attainment >= 80 ? 'bg-green-100' : attainment >= 70 ? 'bg-yellow-100' : 'bg-red-100'
                  }`}>
                    <span className="text-xl font-bold">{attainment}%</span>
                    <div className="absolute inset-0 rounded-full border-4 border-current"
                         style={{ borderRadius: '50%',
                                 backgroundColor: attainment >= 80 ? '#10B981' :
                                                attainment >= 70 ? '#F59E0B' : '#EF4444',
                                 opacity: 0.2 }}></div>
                  </div>
                  <p className="text-sm font-medium capitalize">{level}</p>
                  <p className="text-xs text-gray-500">Level {index + 1}</p>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}

      {/* Performance View */}
      {selectedView === 'performance' && analyticsData && (
        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Exam Performance Analysis</h3>
            <DataTable
              data={analyticsData.examAnalytics}
              columns={[
                {
                  key: 'examTitle',
                  header: 'Exam Title',
                  sortable: true
                },
                {
                  key: 'totalAttempts',
                  header: 'Attempts',
                  render: (value: number) => (
                    <div className="flex items-center gap-1">
                      <UserCircleIcon className="h-4 w-4 text-gray-400" />
                      <span>{value}</span>
                    </div>
                  )
                },
                {
                  key: 'avgScore',
                  header: 'Average Score',
                  render: (value: number) => (
                    <span className={`font-semibold ${value >= 80 ? 'text-green-600' :
                                                   value >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {value}%
                    </span>
                  )
                },
                {
                  key: 'completionRate',
                  header: 'Completion',
                  render: (value: number) => `${value}%`
                },
                {
                  key: 'difficulty',
                  header: 'Difficulty',
                  render: (value: number) => (
                    <div className="flex">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <div
                          key={i}
                          className={`w-2 h-1 mr-0.5 rounded ${
                            i < value ? 'bg-gray-800' : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                  )
                }
              ]}
              loading={false}
              itemsPerPage={10}
              emptyMessage="No exam performance data available"
            />
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Grading Progress</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Currently Being Graded</span>
                    <span>23 / 45</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: '51%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>AI Graded</span>
                    <span>142 / 167</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Manually Graded</span>
                    <span>189 / 201</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{ width: '94%' }}></div>
                  </div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Insights</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                  <span className="text-blue-500 mt-1">📈</span>
                  <div>
                    <p className="text-sm font-medium text-blue-800">Performance Improving</p>
                    <p className="text-xs text-blue-600">Average grades up 3.4% from last month</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
                  <span className="text-yellow-500 mt-1">⚠️</span>
                  <div>
                    <p className="text-sm font-medium text-yellow-800">Attention Needed</p>
                    <p className="text-xs text-yellow-600">Chemistry exam had 32% failure rate</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                  <span className="text-green-500 mt-1">✓</span>
                  <div>
                    <p className="text-sm font-medium text-green-800">Excellent Performance</p>
                    <p className="text-xs text-green-600">Computer Science exams scoring 92%+</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* CO/PO Analysis View */}
      {selectedView === 'co-po' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">CO Attainment Analysis</h3>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => generateCOAttainment()}
                >
                  Generate Report
                </Button>
              </div>
              <div className="space-y-4">
                <div className="text-sm text-gray-600">
                  Detailed analysis of Course Outcome attainment levels across all subjects.
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-blue-800">Knowledge (CO1)</span>
                    <span className="text-sm font-bold text-blue-800">85%</span>
                  </div>
                  <div className="w-full bg-blue-200 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-green-800">Analysis (CO4)</span>
                    <span className="text-sm font-bold text-green-800">76%</span>
                  </div>
                  <div className="w-full bg-green-200 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '76%' }}></div>
                  </div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">PO Attainment Analysis</h3>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => generatePOAttainment()}
                >
                  Generate Report
                </Button>
              </div>
              <div className="space-y-4">
                <div className="text-sm text-gray-600">
                  Program Outcome attainment aligned with accreditation standards.
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-purple-800">PO1: Engineering Knowledge</span>
                    <span className="text-sm font-bold text-purple-800">82%</span>
                  </div>
                  <div className="w-full bg-purple-200 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{ width: '82%' }}></div>
                  </div>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-yellow-800">PO12: Life-long Learning</span>
                    <span className="text-sm font-bold text-yellow-800">74%</span>
                  </div>
                  <div className="w-full bg-yellow-200 rounded-full h-2">
                    <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '74%' }}></div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Reports View */}
      {selectedView === 'reports' && (
        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Generate Reports</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Button
                variant="secondary"
                onClick={() => exportAnalytics('pdf')}
                className="flex items-center gap-3 p-6 h-auto"
              >
                <DocumentCheckIcon className="h-8 w-8 text-red-500" />
                <div className="text-left">
                  <div className="font-medium">Academic Performance</div>
                  <div className="text-sm text-gray-600">Complete analysis PDF</div>
                </div>
              </Button>

              <Button
                variant="secondary"
                onClick={() => exportAnalytics('excel')}
                className="flex items-center gap-3 p-6 h-auto"
              >
                <Bars3Icon className="h-8 w-8 text-green-500" />
                <div className="text-left">
                  <div className="font-medium">Grade Sheet</div>
                  <div className="text-sm text-gray-600">Detailed Excel report</div>
                </div>
              </Button>

              <Button
                variant="secondary"
                onClick={() => exportAnalytics('csv')}
                className="flex items-center gap-3 p-6 h-auto"
              >
                <ChartPieIcon className="h-8 w-8 text-blue-500" />
                <div className="text-left">
                  <div className="font-medium">CO/PO Analysis</div>
                  <div className="text-sm text-gray-600">Outcome attainment data</div>
                </div>
              </Button>
            </div>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Reports</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">Monthly Performance Report</p>
                    <p className="text-sm text-gray-600">Generated on Dec 15, 2024</p>
                  </div>
                  <Button variant="secondary" size="sm">Download</Button>
                </div>
                <div className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">CO Attainment Analysis</p>
                    <p className="text-sm text-gray-600">Generated on Dec 10, 2024</p>
                  </div>
                  <Button variant="secondary" size="sm">Download</Button>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Scheduled Reports</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">End Semester Report</p>
                    <p className="text-sm text-gray-600">Due: Dec 31, 2024</p>
                  </div>
                  <Button variant="primary" size="sm">Generate Now</Button>
                </div>
                <div className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">Accreditation Data</p>
                    <p className="text-sm text-gray-600">Due: Jan 15, 2025</p>
                  </div>
                  <Button variant="secondary" size="sm">Schedule</Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
