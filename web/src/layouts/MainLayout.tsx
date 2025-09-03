import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  HomeIcon,
  UserGroupIcon,
  ClipboardDocumentIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { AcademicCapIcon } from '@heroicons/react/24/solid';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  roles: string[];
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, roles: ['admin', 'teacher', 'student'] },
  { name: 'Users', href: '/users', icon: UserGroupIcon, roles: ['admin'] },
  { name: 'Programs', href: '/programs', icon: DocumentTextIcon, roles: ['admin', 'teacher'] },
  { name: 'Exams', href: '/exams', icon: ClipboardDocumentIcon, roles: ['admin', 'teacher', 'student'] },
  { name: 'Questions', href: '/questions', icon: DocumentTextIcon, roles: ['admin', 'teacher'] },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon, roles: ['admin', 'teacher'] },
  { name: 'Audit', href: '/audit', icon: CogIcon, roles: ['admin'] },
];

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const filteredNavigation = navigation.filter(item =>
    user && item.roles.includes(user.role)
  );

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 flex z-40 md:hidden ${sidebarOpen ? '' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex-flex-col flex-1 mx-4 mt-5 bg-white rounded-t-lg shadow-lg divide-y divide-gray-200">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <AcademicCapIcon className="h-8 w-8 text-blue-600" />
                <span className="text-xl font-bold text-gray-900">DSBA LMS</span>
              </div>
              <button onClick={() => setSidebarOpen(false)}>
                <XMarkIcon className="h-6 w-6 text-gray-400" />
              </button>
            </div>
          </div>
          <nav className="px-6 pb-6 pt-5">
            {filteredNavigation.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className="flex items-center px-3 py-2 text-base font-medium text-gray-900 rounded-md hover:bg-gray-50 hover:text-blue-600"
              >
                <item.icon className="mr-3 h-5 w-5 text-gray-400" />
                {item.name}
              </a>
            ))}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 bg-white border-r border-gray-200">
          <div className="flex-1 flex flex-col pb-4 overflow-y-auto">
            <div className="flex items-center h-16 flex-shrink-0 px-4 bg-white border-b border-gray-200">
              <AcademicCapIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <span className="text-xl font-bold text-gray-900">DSBA LMS</span>
                <p className="text-xs text-gray-500">
                  {user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'User'} Panel
                </p>
              </div>
            </div>
            <nav className="px-4 mt-8 space-y-1">
              {filteredNavigation.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className="group flex items-center px-2 py-2 text-sm font-medium text-gray-900 rounded-md hover:bg-gray-50 hover:text-blue-600 transition-colors"
                >
                  <item.icon className="mr-3 flexgeh-shrink-0 h-5 w-5 text-gray-400 group-hover:text-blue-600" />
                  {item.name}
                </a>
              ))}
            </nav>
          </div>
          <div className="flex-shrink-0 p-4 border-t border-gray-200">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
              <button
                onClick={logout}
                className="ml-3 p-1 text-gray-400 hover:text-gray-600"
                title="Logout"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="md:pl-64 flex flex-col flex-1">
        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 pl-1 pt-1 sm:pl-3 sm:pt-3 md:pl-5 md:pt-5">
          <button
            type="button"
            className="px-4 py-2 md:hidden text-gray-400 hover:text-gray-500"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
        </div>

        {/* Page content */}
        <main className="flex-1">
          <div className="px-4 py-8 md:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;