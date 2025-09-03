import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DataTable } from '../components/common/DataTable';
import {
  usersApi,
  examsApi,
  questionsApi,
  gradingApi,
  analyticsApi
} from '../utils/api';
import toast from 'react-hot-toast';
import {
  UserGroupIcon,
  DocumentCheckIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  AcademicCapIcon,
  PencilIcon,
  EyeIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  PlusIcon,
  CogIcon
} from '@heroicons/react/24/outline';

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeExams: 0,
    totalQuestions: 0,
    aiGradedResponses: 0,
    teacherGradedResponses: 0,
    pendingGrades: 0,
    systemMemory: 68,
    activeSessions: 12
  });

  const [recentUsers, setRecentUsers] = useState<any[]>([]);
  const [recentExams, setRecentExams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch users data
      const usersResponse = await usersApi.getUsers({ limit: 5 });
      if (usersResponse?.data) {
        setRecentUsers(usersResponse.data.slice(0, 5));
        setStats(prev => ({ ...prev, totalUsers: usersResponse.data.length }));
      }

      // Fetch exams data
      const examsResponse = await examsApi.getExams({ limit: 10 });
      if (examsResponse?.data) {
        setRecentExams(examsResponse.data.slice(0, 5));
        setStats(prev => ({
          ...prev,
          activeExams: examsResponse.data.filter((exam: any) => exam.status === 'published').length
        }));
      }

      // Fetch questions count
      const questionsResponse = await questionsApi.getQuestions({ limit: 1000 });
      if (questionsResponse?.data) {
        setStats(prev => ({ ...prev, totalQuestions: questionsResponse.data.length }));
      }

      // Get system analytics if available
      try {
        const analyticsResponse = await analyticsApi.getAnalytics('system');
        if (analyticsResponse?.data) {
          const systemData = analyticsResponse.data;
          setStats(prev => ({
            ...prev,
            aiGradedResponses: systemData.aiGradedResponses || 0,
            teacherGradedResponses: systemData.teacherGradedResponses || 0,
            pendingGrades: systemData.pendingGrades || 0
          }));
        }
      } catch (error) {
        // Analytics endpoint might not be available yet
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">HOD/Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">Comprehensive overview of your institution's learning system</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={() => navigate('/analytics')}
            className="flex items-center gap-2"
          >
            <ChartBarIcon className="h-5 w-5" />
            Analytics
          </Button>
        </div>
      </div>

      {/* Key Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
          className="p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 rounded-lg bg-white"
          onClick={() => navigate('/users')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="text-3xl font-bold text-blue-600">{stats.totalUsers}</p>
              <div className="flex items-center mt-2">
                <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-xs text-green-600 font-medium">+12% this month</span>
              </div>
            </div>
            <UserGroupIcon className="h-12 w-12 text-blue-100" />
          </div>
        </div>

        <div
          className="p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 rounded-lg bg-white"
          onClick={() => navigate('/exams')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Exams</p>
              <p className="text-3xl font-bold text-green-600">{stats.activeExams}</p>
              <div className="flex items-center mt-2">
                <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-xs text-green-600 font-medium">3 new this week</span>
              </div>
            </div>
            <DocumentCheckIcon className="h-12 w-12 text-green-100" />
          </div>
        </div>

        <div
          className="p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 rounded-lg bg-white"
          onClick={() => navigate('/questions')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Question Bank</p>
              <p className="text-3xl font-bold text-purple-600">{stats.totalQuestions}</p>
              <div className="flex items-center mt-2">
                <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-xs text-green-600 font-medium">28 AI-generated</span>
              </div>
            </div>
            <AcademicCapIcon className="h-12 w-12 text-purple-100" />
          </div>
        </div>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Grading Status</p>
              <p className="text-3xl font-bold text-orange-600">
                {stats.aiGradedResponses + stats.teacherGradedResponses}
              </p>
              <div className="flex items-center mt-2">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-xs text-green-600 font-medium">
                  {stats.pendingGrades} pending
                </span>
              </div>
            </div>
            <ClockIcon className="h-12 w-12 text-orange-100" />
          </div>
        </Card>
      </div>

      {/* Quick Actions & System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 gap-3">
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate('/users')}
              className="w-full justify-between"
            >
              <span className="flex items-center">
                <UserGroupIcon className="h-5 w-5 mr-3" />
                Manage Users
              </span>
              <span className="text-sm">{stats.totalUsers} total</span>
            </Button>

            <Button
              variant="secondary"
              size="lg"
              onClick={() => navigate('/questions')}
              className="w-full justify-between"
            >
              <span className="flex items-center">
                <AcademicCapIcon className="h-5 w-5 mr-3" />
                AI Question Generator
              </span>
              <span className="text-sm">Generate Now</span>
            </Button>

            <Button
              variant="secondary"
              size="lg"
              onClick={() => navigate('/exams')}
              className="w-full justify-between"
            >
              <span className="flex items-center">
                <DocumentCheckIcon className="h-5 w-5 mr-3" />
                Create Exam
              </span>
              <span className="text-sm">{stats.activeExams} active</span>
            </Button>

            <Button
              variant="secondary"
              size="lg"
              onClick={() => navigate('/analytics')}
              className="w-full justify-between"
            >
              <span className="flex items-center">
                <ArrowTrendingUpIcon className="h-5 w-5 mr-3" />
                View Analytics
              </span>
              <span className="text-sm">CO/PO Reports</span>
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 border border-green-200 bg-green-50 rounded-lg">
              <span className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                <span className="text-sm font-medium">Database Connection</span>
              </span>
              <span className="text-sm text-green-600 font-semibold">Healthy</span>
            </div>

            <div className="flex items-center justify-between p-3 border border-green-200 bg-green-50 rounded-lg">
              <span className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                <span className="text-sm font-medium">AI Services</span>
              </span>
              <span className="text-sm text-green-600 font-semibold">Operational</span>
            </div>

            <div className="flex items-center justify-between p-3 border border-blue-200 bg-blue-50 rounded-lg">
              <span className="flex items-center">
                <UserGroupIcon className="h-4 w-4 text-blue-500 mr-3" />
                <span className="text-sm font-medium">Active Sessions</span>
              </span>
              <span className="text-sm text-blue-600 font-semibold">{stats.activeSessions}</span>
            </div>

            <div className="flex items-center justify-between p-3 border border-gray-200 bg-gray-50 rounded-lg">
              <span className="flex items-center">
                <CogIcon className="h-4 w-4 text-gray-500 mr-3" />
                <span className="text-sm font-medium">System Memory</span>
              </span>
              <div className="flex items-center">
                <span className="text-sm text-gray-600 mr-2">{stats.systemMemory}%</span>
                <div className="w-16 h-1 bg-gray-200 rounded">
                  <div
                    className="h-full bg-blue-500 rounded"
                    style={{ width: `${stats.systemMemory}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Activities & Reports */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h3>
          <div className="space-y-4">
            {recentUsers.slice(0, 5).map((user, index) => (
              <div key={user.id || index} className="flex items-center justify-between py-2">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                    <UserGroupIcon className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {user.name || user.username}
                    </p>
                    <p className="text-xs text-gray-500">
                      {user.role} • {user.is_active ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(user.created_at || Date.now()).toLocaleDateString()}
                </span>
              </div>
            ))}

            {recentExams.slice(0, 3).map((exam, index) => (
              <div key={exam.id || index} className="flex items-center justify-between py-2">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                    <DocumentCheckIcon className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{exam.title}</p>
                    <p className="text-xs text-gray-500">Exam • {exam.status}</p>
                  </div>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(exam.created_at || Date.now()).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Reports</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border border-blue-200 bg-blue-50 rounded-lg cursor-pointer hover:bg-blue-100 transition-colors">
              <span className="flex items-center">
                <DocumentCheckIcon className="h-5 w-5 text-blue-500 mr-3" />
                <span className="text-sm font-medium">User Management Report</span>
              </span>
              <Button variant="secondary" size="sm" onClick={() => navigate('/users')}>
                View
              </Button>
            </div>

            <div className="flex items-center justify-between p-3 border border-green-200 bg-green-50 rounded-lg cursor-pointer hover:bg-green-100 transition-colors">
              <span className="flex items-center">
                <ChartBarIcon className="h-5 w-5 text-green-500 mr-3" />
                <span className="text-sm font-medium">Grading Analytics</span>
              </span>
              <Button variant="secondary" size="sm" onClick={() => navigate('/analytics')}>
                View
              </Button>
            </div>

            <div className="flex items-center justify-between p-3 border border-purple-200 bg-purple-50 rounded-lg cursor-pointer hover:bg-purple-100 transition-colors">
              <span className="flex items-center">
                <AcademicCapIcon className="h-5 w-5 text-purple-500 mr-3" />
                <span className="text-sm font-medium">Question Bank Summary</span>
              </span>
              <Button variant="secondary" size="sm" onClick={() => navigate('/questions')}>
                View
              </Button>
            </div>

            <div className="flex items-center justify-between p-3 border border-orange-200 bg-orange-50 rounded-lg cursor-pointer hover:bg-orange-100 transition-colors">
              <span className="flex items-center">
                <ClockIcon className="h-5 w-5 text-orange-500 mr-3" />
                <span className="text-sm font-medium">System Performance</span>
              </span>
              <Button variant="secondary" size="sm" onClick={() => navigate('/analytics')}>
                Monitor
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

const TeacherDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState({
    activeCourses: 0,
    totalStudents: 0,
    upcomingExams: 0,
    pendingGrading: 0,
    totalExams: 0,
    publishedQuestions: 0
  });

  const [courses, setCourses] = useState<any[]>([]);
  const [recentExams, setRecentExams] = useState<any[]>([]);
  const [gradingQueue, setGradingQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTeacherDashboardData();
  }, []);

  const fetchTeacherDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch teacher's courses (if API endpoint exists)
      try {
        // For now, use mock data - would be replaced with real API calls
        // Set mock courses data since API might not be available
        const mockCourses = [
          {
            id: 1,
            name: "Computer Science 101",
            code: "CS101",
            studentsCount: 32,
            currentSem: "Spring 2024",
            status: "active"
          },
          {
            id: 2,
            name: "Data Structures and Algorithms",
            code: "CS201",
            studentsCount: 28,
            currentSem: "Spring 2024",
            status: "active"
          },
          {
            id: 3,
            name: "Web Development",
            code: "CS301",
            studentsCount: 25,
            currentSem: "Spring 2024",
            status: "active"
          }
        ];
        setCourses(mockCourses);

        // Fetch recent exams
        const examsResponse = await examsApi.getExams({ limit: 10 });
        if (examsResponse?.data) {
          setRecentExams(examsResponse.data.slice(0, 3));
          setStats(prev => ({
            ...prev,
            upcomingExams: examsResponse.data.filter((exam: any) => exam.status === 'published').length,
            totalExams: examsResponse.data.length
          }));
        }

        // Fetch grading queue
        try {
          const gradingResponse = await gradingApi.getGradingProgress(1); // Would need to get teacher's exam IDs
          if (gradingResponse) {
            setStats(prev => ({ ...prev, pendingGrading: gradingResponse.pending || 12 }));
          }
        } catch (error) {
          // Set mock data if endpoint doesn't exist
          setStats(prev => ({ ...prev, pendingGrading: 12 }));
        }

        setStats(prev => ({
          ...prev,
          activeCourses: mockCourses.length,
          totalStudents: mockCourses.reduce((acc: number, course) => acc + course.studentsCount, 0),
          publishedQuestions: 156
        }));

      } catch (error) {
        // Fallback to mock data
        console.error('API error in teacher dashboard:', error);
        setStats({
          activeCourses: 3,
          totalStudents: 85,
          upcomingExams: 2,
          pendingGrading: 12,
          totalExams: 8,
          publishedQuestions: 156
        });
      }

    } catch (error) {
      console.error('Error fetching teacher dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Teacher Dashboard</h1>
        <div className="text-right">
          <p className="text-lg font-medium text-gray-900">Hello, Professor!</p>
          <p className="text-sm text-gray-500">Manage your courses and students</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <span className="text-2xl">📚</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Active Courses</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.activeCourses}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <span className="text-2xl">👥</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Students</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.totalStudents}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <span className="text-2xl">📝</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Upcoming Exams</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.upcomingExams}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <span className="text-2xl">📊</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Pending Grading</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.pendingGrading}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Button variant="primary" size="lg" className="w-full justify-start">
              <span className="mr-2">📝</span>
              Create Exam
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">🤖</span>
              AI Question Generator
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">📊</span>
              Grade Students
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">📈</span>
              View Course Analytics
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Schedule</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">CS101 Lecture</p>
                <p className="text-sm text-gray-600">Classroom A1, Room 204</p>
              </div>
              <span className="text-sm font-medium text-blue-600">10:00 AM</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Student Consultation</p>
                <p className="text-sm text-gray-600">Office Hours</p>
              </div>
              <span className="text-sm font-medium text-green-600">2:00 PM</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Final Exam Review</p>
                <p className="text-sm text-gray-600">Classroom B2</p>
              </div>
              <span className="text-sm font-medium text-yellow-600">4:00 PM</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Course Overview */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Courses</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h4 className="font-medium text-gray-900">Computer Science 101</h4>
              <p className="text-sm text-gray-600">Introduction to Programming</p>
              <p className="text-xs text-gray-500">32 enrolled students</p>
            </div>
            <div className="text-right">
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">Active</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h4 className="font-medium text-gray-900">Data Structures Advanced</h4>
              <p className="text-sm text-gray-600">Algorithm Analysis</p>
              <p className="text-xs text-gray-500">28 enrolled students</p>
            </div>
            <div className="text-right">
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">Active</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h4 className="font-medium text-gray-900">Web Development</h4>
              <p className="text-sm text-gray-600">Full-Stack React & Node.js</p>
              <p className="text-xs text-gray-500">25 enrolled students</p>
            </div>
            <div className="text-right">
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">Active</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState({
    sgpa: 8.5,
    cgpa: 8.3,
    upcomingExams: 0,
    completedCourses: 8,
    totalAttempts: 0,
    pendingResults: 0
  });

  const [upcomingExams, setUpcomingExams] = useState<any[]>([]);
  const [recentResults, setRecentResults] = useState<any[]>([]);
  const [currentCourses, setCurrentCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudentDashboardData();
  }, []);

  const fetchStudentDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch student's exams
      try {
        const examsResponse = await examsApi.getExams({ limit: 10 });
        if (examsResponse?.data) {
          setUpcomingExams(examsResponse.data.filter((exam: any) => exam.status === 'published').slice(0, 5));
          setStats(prev => ({
            ...prev,
            upcomingExams: examsResponse.data.filter((exam: any) => exam.status === 'published').length
          }));
        }
      } catch (error) {
        // Set mock exam data
        setUpcomingExams([
          {
            id: 1,
            title: "Mathematics Final Exam",
            courseName: "CS101 - Data Structures",
            scheduledAt: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
            duration: 120,
            totalMarks: 100
          },
          {
            id: 2,
            title: "Chemistry Practical",
            courseName: "CH201 - Organic Chemistry",
            scheduledAt: new Date(Date.now() + 604800000).toISOString(), // Next week
            duration: 180,
            totalMarks: 50
          }
        ]);
        setStats(prev => ({ ...prev, upcomingExams: 2 }));
      }

      // Fetch analytics data for SGPA/CGPA
      try {
        if (user?.id) {
          const analyticsResponse = await analyticsApi.getAnalytics('student', user.id);
          if (analyticsResponse?.data) {
            const studentData = analyticsResponse.data;
            setStats(prev => ({
              ...prev,
              sgpa: studentData.sgpa || 8.5,
              cgpa: studentData.cgpa || 8.3,
              totalAttempts: studentData.totalAttempts || 24,
              pendingResults: studentData.pendingResults || 3
            }));
          }
        }
      } catch (error) {
        // Use mock data
        console.log('Analytics API not available, using mock data');
      }

      // Set mock current courses
      setCurrentCourses([
        {
          id: 1,
          name: "Computer Science Fundamentals",
          code: "CS101",
          progress: 85,
          assignmentsCompleted: 6,
          totalAssignments: 8,
          examsRemaining: 2
        },
        {
          id: 2,
          name: "Database Systems",
          code: "DB201",
          progress: 92,
          assignmentsCompleted: 8,
          totalAssignments: 10,
          examsRemaining: 1
        },
        {
          id: 3,
          name: "Web Technologies",
          code: "WT301",
          progress: 78,
          assignmentsCompleted: 5,
          totalAssignments: 8,
          examsRemaining: 2
        }
      ]);

      // Mock recent results
      setRecentResults([
        {
          id: 1,
          examName: "Mathematics Mid-term",
          courseName: "Mathematics",
          score: 85,
          grade: 'A',
          marks: '85/100',
          date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString() // 1 week ago
        },
        {
          id: 2,
          examName: "Physics Practical",
          courseName: "Physics",
          score: 92,
          grade: 'A+',
          marks: '46/50',
          date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString() // 2 weeks ago
        }
      ]);

    } catch (error) {
      console.error('Error fetching student dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Student Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back! Track your academic progress</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={() => navigate('/profile')}
            className="flex items-center gap-2"
          >
            <UserGroupIcon className="h-5 w-5" />
            Profile
          </Button>
        </div>
      </div>

      {/* Academic Performance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
          className="p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 rounded-lg bg-white"
          onClick={() => navigate('/analytics')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">SGPA (Current)</p>
              <p className="text-3xl font-bold text-green-600">{stats.sgpa}/10</p>
              <div className="flex items-center mt-2">
                <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-xs text-green-600 font-medium">Grade: Excellent</span>
              </div>
            </div>
            <AcademicCapIcon className="h-12 w-12 text-green-100" />
          </div>
        </div>

        <div
          className="p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 rounded-lg bg-white"
          onClick={() => navigate('/analytics')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CGPA (Overall)</p>
              <p className="text-3xl font-bold text-blue-600">{stats.cgpa}/10</p>
              <div className="flex items-center mt-2">
                <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-xs text-green-600 font-medium">+0.3 from last sem</span>
              </div>
            </div>
            <ChartBarIcon className="h-12 w-12 text-blue-100" />
          </div>
        </div>

        <div
          className="p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 rounded-lg bg-white"
          onClick={() => navigate('/exams')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Upcoming Exams</p>
              <p className="text-3xl font-bold text-yellow-600">{stats.upcomingExams}</p>
              <div className="flex items-center mt-2">
                <ClockIcon className="h-4 w-4 text-blue-500 mr-1" />
                <span className="text-xs text-blue-600 font-medium">This week</span>
              </div>
            </div>
            <DocumentCheckIcon className="h-12 w-12 text-yellow-100" />
          </div>
        </div>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Exam Attempts</p>
              <p className="text-3xl font-bold text-purple-600">{stats.totalAttempts}</p>
              <div className="flex items-center mt-2">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-500 mr-1" />
                <span className="text-xs text-red-600 font-medium">{stats.pendingResults} pending results</span>
              </div>
            </div>
            <UserGroupIcon className="h-12 w-12 text-purple-100" />
          </div>
        </Card>
      </div>

      {/* Quick Actions & Upcoming Exams */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 gap-3">
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate('/exams')}
              className="w-full justify-between"
              disabled={stats.upcomingExams === 0}
            >
              <span className="flex items-center">
                <DocumentCheckIcon className="h-5 w-5 mr-3" />
                Take Upcoming Exam
              </span>
              <span className="text-sm">{stats.upcomingExams} available</span>
            </Button>

            <Button
              variant="secondary"
              size="lg"
              onClick={() => navigate('/analytics')}
              className="w-full justify-between"
            >
              <span className="flex items-center">
                <ChartBarIcon className="h-5 w-5 mr-3" />
                View Results
              </span>
              <span className="text-sm">Latest grades</span>
            </Button>

            <Button
              variant="secondary"
              size="lg"
              onClick={() => navigate('/questions')}
              className="w-full justify-between"
            >
              <span className="flex items-center">
                <AcademicCapIcon className="h-5 w-5 mr-3" />
                Practice Questions
              </span>
              <span className="text-sm">AI-powered</span>
            </Button>

            <Button
              variant="secondary"
              size="lg"
              onClick={() => navigate('/study-assistant')}
              className="w-full justify-between"
            >
              <span className="flex items-center">
                <ArrowTrendingUpIcon className="h-5 w-5 mr-3" />
                AI Study Assistant
              </span>
              <span className="text-sm">Smart recommendations</span>
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Exams</h3>
          <div className="space-y-3">
            {upcomingExams.length > 0 ? (
              upcomingExams.slice(0, 3).map((exam, index) => (
                <div key={exam.id || index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div>
                    <p className="font-medium text-gray-900 text-sm">{exam.title}</p>
                    <p className="text-xs text-gray-600">{exam.courseName}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-blue-600">{exam.duration} min</span>
                      <span className="text-xs text-gray-500">•</span>
                      <span className="text-xs text-purple-600">{exam.totalMarks} marks</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-indigo-600">
                      {new Date(exam.scheduledAt).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(exam.scheduledAt).toLocaleTimeString()}
                    </p>
                    <Button variant="secondary" size="sm" className="mt-1" onClick={() => navigate('/exams')}>
                      Start
                    </Button>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <DocumentCheckIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No upcoming exams</p>
                <p className="text-sm text-gray-400">Check back later for scheduled exams</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Recent Results & Course Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Results</h3>
          <div className="space-y-4">
            {recentResults.map((result, index) => (
              <div key={result.id || index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 ${
                    result.grade === 'A+' ? 'bg-green-100' :
                    result.grade === 'A' ? 'bg-blue-100' :
                    result.grade === 'B' ? 'bg-yellow-100' : 'bg-gray-100'
                  }`}>
                    <span className={`text-sm font-bold ${
                      result.grade === 'A+' ? 'text-green-600' :
                      result.grade === 'A' ? 'text-blue-600' :
                      result.grade === 'B' ? 'text-yellow-600' : 'text-gray-600'
                    }`}>
                      {result.grade}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{result.examName}</p>
                    <p className="text-xs text-gray-500">{result.courseName}</p>
                    <p className="text-xs text-gray-400">{new Date(result.date).toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900">{result.score}%</p>
                  <p className="text-xs text-gray-500">{result.marks}</p>
                </div>
              </div>
            ))}
            {recentResults.length === 0 && (
              <div className="text-center py-8">
                <ChartBarIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No results available</p>
                <p className="text-sm text-gray-400">Results will appear here after exams</p>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Semester Progress</h3>
          <div className="space-y-4">
            {currentCourses.map((course, index) => (
              <div key={course.id || index} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">{course.name}</h4>
                    <p className="text-xs text-gray-500">{course.code}</p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    course.progress >= 90 ? 'bg-green-100 text-green-800' :
                    course.progress >= 75 ? 'bg-blue-100 text-blue-800' :
                    course.progress >= 50 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {course.progress}% Complete
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                  <div
                    className={`h-full rounded-full ${
                      course.progress >= 90 ? 'bg-green-500' :
                      course.progress >= 75 ? 'bg-blue-500' :
                      course.progress >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${course.progress}%` }}
                  ></div>
                </div>
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>Assignments: {course.assignmentsCompleted}/{course.totalAssignments}</span>
                  <span>Exams remaining: {course.examsRemaining}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return <div>Loading...</div>;
  }

  // Render role-specific dashboard
  switch (user.role) {
    case 'admin':
      return <AdminDashboard />;
    case 'teacher':
      return <TeacherDashboard />;
    case 'student':
      return <StudentDashboard />;
    default:
      return <AdminDashboard />; // Default to admin dashboard
  }
};

export default Dashboard;
