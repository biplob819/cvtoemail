import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Globe,
  Briefcase,
  Settings,
  Menu,
  X,
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/cv', label: 'CV Editor', icon: FileText },
  { to: '/sources', label: 'Sources', icon: Globe },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 w-60 bg-white border-r border-border
          flex flex-col transform transition-transform duration-200
          md:relative md:translate-x-0
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Brand */}
        <div className="flex items-center gap-3 px-6 h-16 border-b border-border shrink-0">
          <Briefcase className="size-6 text-primary" />
          <span className="text-base font-semibold text-text">Auto Job Apply</span>
          <button
            className="ml-auto p-1 rounded-md md:hidden hover:bg-surface"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="size-5 text-text-muted" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors mb-1
                ${
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-text-muted hover:text-text hover:bg-surface'
                }`
              }
            >
              <item.icon className="size-5 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border text-xs text-text-muted">
          v0.1.0 &middot; Milestone 1
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar (mobile) */}
        <header className="flex items-center h-16 px-6 border-b border-border bg-white md:hidden shrink-0">
          <button
            className="p-1.5 rounded-md hover:bg-surface"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="size-5 text-text" />
          </button>
          <span className="ml-3 text-base font-semibold text-text">Auto Job Apply</span>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-[960px] mx-auto px-6 md:px-8 py-6 md:py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
