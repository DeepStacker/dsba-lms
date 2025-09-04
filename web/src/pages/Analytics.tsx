import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Select } from '../components/common/Select';
import { PerformanceChart } from '../components/analytics/PerformanceChart';
import { AttainmentChart } from '../components/analytics/AttainmentChart';
import { analyticsApi } from '../utils/api';
import {
  ChartBarIcon,
  DocumentArrowDownIcon,
  AcademicCapIcon,
  UserGroupIcon,
  TrophyIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface AnalyticsData {
  coAttainment: Array<{
    code: string;
    title: string;
    attainment: number;
  }>;
  poAttainment: Array<{
    code: string;
    title: string;
    attainment: number;
  }>;
  performanceTrends: Array<{
    name: string;
    value: number;
  }>;
  gradeDistribution: Array<{
    name: string;
    value: number;
  }>;
}

const Analytics: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('');
  const [selectedProgram, setSelectedProgram] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'co-po' | 'performance' | 'reports'>('overview');

  useEffect(() => {
    fetchAnalyticsData();
  }, [selectedCourse, selectedSemester, selectedProgram]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      // Mock analytics data
      const mockData: AnalyticsData = {
        coAttainment: [
          { code: 'CO1', title: 'Understand basic algorithms', attainment: 85.5 },
          { code: 'CO2', title: 'Implement data structures', attainment: 78.2 },
          { code: 'CO3', title: 'Analyze complexity', attainment: 82.1 },
          { code: 'CO4', title: 'Design efficient solutions', attainment: 76.8 },
          { code: 'CO5', title: 'Apply optimization techniques', attainment: 71.3 }
        ],
        poAttainment: [
          { code: 'PO1', title: 'Engineering knowledge', attainment: 80.5 },
          { code: 'PO2', title: 'Problem analysis', attainment: 75.8 },
          { code: 'PO3', title: 'Design/development', attainment: 77.3 },
          { code: 'PO4', title: 'Investigation', attainment: 72.1 },
          { code: 'PO5', title: 'Modern tool usage', attainment: 83.4 }
        ],
        performanceTrends: [
          { name: 'Jan', value: 75 },
          { name: 'Feb', value: 78 },
          { name: 'Mar', value: 82 },
          { name: 'Apr', value: 79 },
          { name: 'May', value: 85 },
          { name: 'Jun', value: 88 }
        ],
        gradeDistribution: [
          { name: 'O (90-100)', value: 15 },
          { name: 'A+ (80-89)', value: 25 },
          { name: 'A (70-79)', value: 30 },
          { name: 'B+ (60-69)', value: 20 },
          { name: 'B (50-59)', value: 8 },
          { name: 'C (40-49)', value: 2 }
        ]
      };
      setAnalyticsData(mockData);
    } catch (error) {
      toast.error('Failed to fetch analytics data');
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = async (format: 'pdf' | 'csv') => {
    try {
      setLoading(true);
      // Mock export functionality
      toast.success(`Report exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export report');
    } finally {
      setLoading(false);
    }
  };

  const getAttainmentColor = (attainment: number) => {
    if (attainment >= 80) return 'text-green-600';
    if (attainment >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getAttainmentStatus = (attainment: number) => {
    if (attainment >= 80) return 'Excellent';
    if (attainment >= 60) return 'Good';
    return 'Needs Improvement';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Analytics & Reports</h1>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={() => handleExportReport('csv')}
            className="flex items-center gap-2"
          >
            <DocumentArrowDownIcon className="h-5 w-5" />
            Export CSV
          </Button>
          <Button
            variant="primary"
            onClick={() => handleExportReport('pdf')}
            className="flex items-center gap-2"
          >
            <DocumentArrowDownIcon className="h-5 w-5" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Select
            label="Program"
            value={selectedProgram}
            onChange={setSelectedProgram}
            options={[
              { value: '', label: 'All Programs' },
              { value: '1', label: 'Bachelor of Computer Applications' },
              { value: '2', label: 'Master of Computer Applications' }
            ]}
          />
          <Select
            label="Course"
            value={selectedCourse}
            onChange={setSelectedCourse}
            options={[
              { value: '', label: 'All Courses' },
              { value: '1', label: 'Data Structures and Algorithms' },
              { value: '2', label: 'Database Management Systems' },
              { value: '3', label: 'Web Development' }
            ]}
          />
          <Select
            label="Semester"
            value={selectedSemester}
            onChange={setSelectedSemester}
            options={[
              { value: '', label: 'All Semesters' },
              { value: '1', label: 'Semester 1' },
              { value: '2', label: 'Semester 2' },
              { value: '3', label: 'Semester 3' },
              { value: '4', label: 'Semester 4' }
            ]}
          />
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: ChartBarIcon },
            { id: 'co-po', label: 'CO/PO Analysis', icon: AcademicCapIcon },
            { id: 'performance', label: 'Performance Trends', icon: TrophyIcon },
            { id: 'reports', label: 'Detailed Reports', icon: DocumentArrowDownIcon }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-blue-100">
                  <AcademicCapIcon className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Average CO Attainment</h3>
                  <p className="text-2xl font-bold text-blue-600">78.8%</p>
                </div>
              </div>
            </Card>
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-green-100">
                  <TrophyIcon className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Average PO Attainment</h3>
                  <p className="text-2xl font-bold text-green-600">77.8%</p>
                </div>
              </div>
            </Card>
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-purple-100">
                  <UserGroupIcon className="h-8 w-8 text-purple-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Students Analyzed</h3>
                  <p className="text-2xl font-bold text-purple-600">245</p>
                </div>
              </div>
            </Card>
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-yellow-100">
                  <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">At-Risk Students</h3>
                  <p className="text-2xl font-bold text-yellow-600">12</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PerformanceChart
              title="Performance Trends"
              data={analyticsData?.performanceTrends || []}
              type="line"
              color="#3b82f6"
            />
            <PerformanceChart
              title="Grade Distribution"
              data={analyticsData?.gradeDistribution || []}
              type="bar"
              color="#10b981"
            />
          </div>
        </div>
      )}

      {activeTab === 'co-po' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AttainmentChart
              title="Course Outcome (CO) Attainment"
              data={analyticsData?.coAttainment || []}
              type="CO"
            />
            <AttainmentChart
              title="Program Outcome (PO) Attainment"
              data={analyticsData?.poAttainment || []}
              type="PO"
            />
          </div>

          {/* Detailed CO/PO Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">CO Attainment Details</h3>
              <div className="space-y-3">
                {analyticsData?.coAttainment.map((co, index) => (
                  <div key={index} className="flex justify-between items-center p-3 border border-gray-200 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">{co.code}</div>
                      <div className="text-sm text-gray-600">{co.title}</div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${getAttainmentColor(co.attainment)}`}>
                        {co.attainment.toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">
                        {getAttainmentStatus(co.attainment)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">PO Attainment Details</h3>
              <div className="space-y-3">
                {analyticsData?.poAttainment.map((po, index) => (
                  <div key={index} className="flex justify-between items-center p-3 border border-gray-200 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">{po.code}</div>
                      <div className="text-sm text-gray-600">{po.title}</div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${getAttainmentColor(po.attainment)}`}>
                        {po.attainment.toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">
                        {getAttainmentStatus(po.attainment)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'performance' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            <PerformanceChart
              title="Monthly Performance Trends"
              data={analyticsData?.performanceTrends || []}
              type="line"
              color="#3b82f6"
              className="h-96"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performers</h3>
              <div className="space-y-3">
                {[
                  { name: 'Alice Johnson', score: 95.2, course: 'Data Structures' },
                  { name: 'Bob Smith', score: 92.8, course: 'Database Systems' },
                  { name: 'Carol Davis', score: 91.5, course: 'Web Development' },
                  { name: 'David Wilson', score: 90.3, course: 'Data Structures' },
                  { name: 'Eva Brown', score: 89.7, course: 'Database Systems' }
                ].map((student, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">{student.name}</div>
                      <div className="text-sm text-gray-600">{student.course}</div>
                    </div>
                    <div className="text-lg font-bold text-green-600">
                      {student.score}%
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Areas for Improvement</h3>
              <div className="space-y-3">
                {[
                  { area: 'Algorithm Optimization', score: 65.2, students: 23 },
                  { area: 'Database Design', score: 68.8, students: 18 },
                  { area: 'Code Quality', score: 71.5, students: 15 },
                  { area: 'Problem Solving', score: 73.3, students: 12 },
                  { area: 'Testing Strategies', score: 74.7, students: 9 }
                ].map((area, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">{area.area}</div>
                      <div className="text-sm text-gray-600">{area.students} students affected</div>
                    </div>
                    <div className="text-lg font-bold text-red-600">
                      {area.score}%
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'reports' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="p-6 cursor-pointer hover:shadow-lg transition-shadow">
              <div className="flex items-center mb-4">
                <AcademicCapIcon className="h-8 w-8 text-blue-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">CO Attainment Report</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Detailed course outcome attainment analysis with student-wise breakdown
              </p>
              <Button variant="primary" size="sm" className="w-full">
                Generate Report
              </Button>
            </Card>

            <Card className="p-6 cursor-pointer hover:shadow-lg transition-shadow">
              <div className="flex items-center mb-4">
                <TrophyIcon className="h-8 w-8 text-green-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">PO Attainment Report</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Program outcome attainment with mapping to course outcomes
              </p>
              <Button variant="primary" size="sm" className="w-full">
                Generate Report
              </Button>
            </Card>

            <Card className="p-6 cursor-pointer hover:shadow-lg transition-shadow">
              <div className="flex items-center mb-4">
                <UserGroupIcon className="h-8 w-8 text-purple-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">Student Performance</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Individual student performance analysis and recommendations
              </p>
              <Button variant="primary" size="sm" className="w-full">
                Generate Report
              </Button>
            </Card>

            <Card className="p-6 cursor-pointer hover:shadow-lg transition-shadow">
              <div className="flex items-center mb-4">
                <ChartBarIcon className="h-8 w-8 text-yellow-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">Grade Distribution</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Statistical analysis of grade distribution across courses
              </p>
              <Button variant="primary" size="sm" className="w-full">
                Generate Report
              </Button>
            </Card>

            <Card className="p-6 cursor-pointer hover:shadow-lg transition-shadow">
              <div className="flex items-center mb-4">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">At-Risk Students</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Identification and analysis of students requiring intervention
              </p>
              <Button variant="primary" size="sm" className="w-full">
                Generate Report
              </Button>
            </Card>

            <Card className="p-6 cursor-pointer hover:shadow-lg transition-shadow">
              <div className="flex items-center mb-4">
                <DocumentArrowDownIcon className="h-8 w-8 text-indigo-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">Comprehensive Report</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Complete institutional analytics report for accreditation
              </p>
              <Button variant="primary" size="sm" className="w-full">
                Generate Report
              </Button>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;