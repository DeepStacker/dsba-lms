import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

// Role-specific dashboard components
const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeExams: 0,
    programsCount: 0,
    pendingGrades: 0
  });

  useEffect(() => {
    // Mock data - replace with real API calls
    setStats({
      totalUsers: 45,
      activeExams: 8,
      programsCount: 5,
      pendingGrades: 23
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">HOD/Admin Dashboard</h1>
        <div className="text-right">
          <p className="text-lg font-medium text-gray-900">Welcome!</p>
          <p className="text-sm text-gray-500">Manage your institution's learning system</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <span className="text-2xl">👥</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Users</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.totalUsers}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <span className="text-2xl">📝</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Active Exams</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.activeExams}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <span className="text-2xl">📚</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Programs</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.programsCount}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <span className="text-2xl">🔔</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Pending Grades</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.pendingGrades}</p>
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
              <span className="mr-2">👥</span>
              Manage Users
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">📚</span>
              Create Program
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">📊</span>
              View Analytics
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">📋</span>
              Export Reports
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Database Connection</span>
              <span className="text-green-600 font-medium">✓ Connected</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">AI Services</span>
              <span className="text-green-600 font-medium">✓ Running</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Active Sessions</span>
              <span className="text-blue-600 font-medium">12 users</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">System Memory</span>
              <span className="text-green-600 font-medium">68% free</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Activities */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span className="text-gray-600">New user registered: John Doe (Student)</span>
            <span className="text-xs text-gray-400 ml-auto">2 minutes ago</span>
          </div>
          <div className="flex items-center space-x-3">
            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
            <span className="text-gray-600">Exam "Mathematics Final" created</span>
            <span className="text-xs text-gray-400 ml-auto">15 minutes ago</span>
          </div>
          <div className="flex items-center space-x-3">
            <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
            <span className="text-gray-600">Grades submitted for Chemistry assignment</span>
            <span className="text-xs text-gray-400 ml-auto">1 hour ago</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

const TeacherDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    activeCourses: 3,
    totalStudents: 25,
    upcomingExams: 2,
    pendingGrading: 12
  });

  useEffect(() => {
    // In a real app, fetch from API
    setStats({
      activeCourses: 3,
      totalStudents: 25,
      upcomingExams: 2,
      pendingGrading: 12
    });
  }, []);

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
  const [stats, setStats] = useState({
    sgpa: 8.5,
    cgpa: 8.3,
    upcomingExams: 3,
    completedCourses: 8
  });

  useEffect(() => {
    // In a real app, fetch from API
    setStats({
      sgpa: 8.5,
      cgpa: 8.3,
      upcomingExams: 3,
      completedCourses: 8
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Student Dashboard</h1>
        <div className="text-right">
          <p className="text-lg font-medium text-gray-900">Welcome back!</p>
          <p className="text-sm text-gray-500">Track your academic progress</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <span className="text-2xl">🎯</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">SGPA</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.sgpa}/10</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <span className="text-2xl">📈</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">CGPA</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.cgpa}/10</p>
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
            <div className="p-2 bg-purple-100 rounded-lg">
              <span className="text-2xl">📚</span>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Completed Courses</h3>
              <p className="text-2xl font-bold text-gray-900">{stats.completedCourses}</p>
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
              Take Upcoming Exam
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">📊</span>
              View Results
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">🎯</span>
              Check SGPA/CGPA
            </Button>
            <Button variant="secondary" size="lg" className="w-full justify-start">
              <span className="mr-2">🚀</span>
              AI Study Assistant
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Exams</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Mathematics Final Exam</p>
                <p className="text-sm text-gray-600">CS101 - Data Structures</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium text-red-600">Tomorrow</span>
                <p className="text-xs text-gray-500">10:00 AM</p>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Chemistry Practical</p>
                <p className="text-sm text-gray-600">CH201 - Organic Chemistry</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium text-orange-600">Wed May 15</span>
                <p className="text-xs text-gray-500">2:00 PM</p>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Physics Theory Paper</p>
                <p className="text-sm text-gray-600">PHY301 - Quantum Physics</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium text-green-600">Fri May 17</span>
                <p className="text-xs text-gray-500">9:00 AM</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Course Progress */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Semester Progress</h3>
        <div className="space-y-4">
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Computer Science Fundamentals</h4>
              <span className="text-sm font-medium text-blue-600">85% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '85%' }}></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">6 assignments completed, 2 exams remaining</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Database Systems</h4>
              <span className="text-sm font-medium text-green-600">92% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-green-600 h-2 rounded-full" style={{ width: '92%' }}></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">8 assignments completed, final exam this week</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Web Technologies</h4>
              <span className="text-sm font-medium text-yellow-600">78% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-yellow-600 h-2 rounded-full" style={{ width: '78%' }}></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">5 assignments completed, 3 pending</p>
          </div>
        </div>
      </Card>
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
