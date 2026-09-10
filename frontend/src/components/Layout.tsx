import { Outlet, NavLink, Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { ClipboardList, LayoutDashboard, LogOut, Menu, Plus, X, Bell, Moon, Sun, Settings, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navigation = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/inspections', label: 'Inspections', icon: ClipboardList },
];

const pageTitles: Record<string, { eyebrow: string; title: string }> = {
  '/dashboard': { eyebrow: 'Compliance Workspace', title: 'Operations overview' },
  '/inspections': { eyebrow: 'Inspection Register', title: 'Inspection records' },
  '/inspections/new': { eyebrow: 'Case Intake', title: 'Create inspection' },
  '/profile': { eyebrow: 'Account', title: 'Your profile' },
  '/settings': { eyebrow: 'Account', title: 'Settings' },
};

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [desktopCollapsed, setDesktopCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(() => document.documentElement.classList.contains('dark'));
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: 1, message: 'Inspection INS-002 requires your review.', time: '10 minutes ago' },
    { id: 2, message: 'New rule violation detected in workspace.', time: '1 hour ago' }
  ]);

  const current = pageTitles[location.pathname] ?? { eyebrow: 'Evidence-led assessment', title: 'Inspection workspace' };
  const initials = user?.name?.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() || 'IN';

  const signOut = () => { logout(); navigate('/login'); };

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [darkMode]);

  const navigationContent = (
    <>
      <div className={`flex h-20 items-center gap-3 border-b border-[var(--sidebar-line)] ${desktopCollapsed ? 'justify-center px-0' : 'px-6'}`}>
        <img src="/logo.jpeg" alt="CompliQ Logo" className="h-9 w-9 rounded-lg bg-white object-contain p-1 shrink-0" />
        {!desktopCollapsed && (
          <div className="overflow-hidden transition-all duration-300 whitespace-nowrap">
            <p className="text-sm font-bold tracking-[.15em] text-[var(--sidebar-text)]">COMPLIQ</p>
            <p className="text-[10px] uppercase tracking-wider text-[var(--sidebar-text-faint)] mt-0.5">Compliance Workspace</p>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto py-6">
        <div className={`mb-6 ${desktopCollapsed ? 'px-2' : 'px-4'}`}>
          <NavLink
            to="/inspections/new"
            onClick={() => setMobileOpen(false)}
            title={desktopCollapsed ? "New inspection" : undefined}
            className={`flex items-center justify-center gap-2 rounded-lg bg-[var(--brand)] py-3 text-sm font-semibold text-white transition-colors hover:bg-[var(--brand-hover)] w-full ${desktopCollapsed ? 'px-0' : 'px-4'}`}
          >
            <Plus size={18} className={desktopCollapsed ? '' : 'shrink-0'} /> {!desktopCollapsed && "New inspection"}
          </NavLink>
        </div>

        {!desktopCollapsed && (
          <div className="px-4 mb-3 mt-2">
            <p className="px-2 text-[10px] font-bold uppercase tracking-[.15em] text-[var(--sidebar-text-faint)]">Workspace</p>
          </div>
        )}

        <nav className={`space-y-1 ${desktopCollapsed ? 'px-2' : 'px-3'}`} aria-label="Primary navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              title={desktopCollapsed ? label : undefined}
              className={({ isActive }) => `
                group flex items-center gap-3 rounded-lg py-3 text-sm font-medium transition-colors duration-200 border-l-2
                ${desktopCollapsed ? 'justify-center px-0 border-l-0' : 'px-3'}
                ${isActive
                  ? 'border-[var(--brand)] bg-[var(--sidebar-surface)] text-white'
                  : 'border-transparent text-[var(--sidebar-text-muted)] hover:bg-[var(--sidebar-surface)] hover:text-white'
                }
              `}
            >
              {({ isActive }) => (
                <>
                  <Icon size={18} className={isActive ? 'text-white' : 'text-[var(--sidebar-text-muted)] group-hover:text-white transition-colors'} />
                  {!desktopCollapsed && label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className={`border-t border-[var(--sidebar-line)] ${desktopCollapsed ? 'p-2' : 'p-4'}`}>
        {!desktopCollapsed && (
          <div className="mb-4 flex items-center gap-3 px-2">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[var(--brand)] text-xs font-bold text-white">
              {initials}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-[var(--sidebar-text)]">{user?.name}</p>
            </div>
          </div>
        )}
        <button
          className={`flex w-full items-center gap-2 rounded-lg py-2.5 text-sm font-medium text-[var(--sidebar-text-muted)] transition-colors hover:bg-white/5 hover:text-white ${desktopCollapsed ? 'justify-center px-0' : 'px-3'}`}
          onClick={signOut}
          title={desktopCollapsed ? "Sign out" : undefined}
        >
          <LogOut size={16} /> {!desktopCollapsed && "Sign out"}
        </button>
      </div>
    </>
  );

  return (
    <div className="app-shell flex bg-[var(--canvas)] transition-colors duration-300">
      {/* Desktop Sidebar */}
      <aside className={`sticky top-0 hidden h-screen shrink-0 flex-col bg-[var(--sidebar-bg)] lg:flex z-40 transition-all duration-300 ease-in-out ${desktopCollapsed ? 'w-20' : 'w-64'}`}>
        {navigationContent}
      </aside>

      {/* Mobile Sidebar */}
      {mobileOpen && (
        <button className="fixed inset-0 z-40 bg-[var(--sidebar-bg)]/80 backdrop-blur-sm lg:hidden" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />
      )}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-[var(--sidebar-bg)] shadow-2xl transition-transform duration-300 ease-out lg:hidden ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`} aria-label="Mobile navigation">
        {navigationContent}
      </aside>

      {/* Main Content Area */}
      <div className="min-w-0 flex-1 flex flex-col h-screen overflow-hidden">

        {/* Top Navigation Layer */}
        <header className="sticky top-0 z-30 flex h-20 shrink-0 items-center justify-between border-b border-[var(--line)] bg-[var(--canvas)]/80 backdrop-blur-md px-4 lg:px-10 transition-colors duration-300">
          <div className="flex items-center gap-4">
            <button className="ui-icon-button" onClick={() => {
              if (window.innerWidth >= 1024) setDesktopCollapsed(!desktopCollapsed);
              else setMobileOpen(!mobileOpen);
            }} aria-label="Toggle navigation">
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <div className="hidden sm:block">
              <p className="text-kicker text-[var(--brand)]">{current.eyebrow}</p>
              <h1 className="text-xl font-semibold tracking-tight text-[var(--text)] mt-0.5">{current.title}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <button className="ui-icon-button" onClick={() => setDarkMode(!darkMode)} title="Toggle theme">
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <div className="relative">
              <button className="ui-icon-button relative" onClick={() => { setNotificationsOpen(!notificationsOpen); setProfileOpen(false); }}>
                <Bell size={18} />
                {notifications.length > 0 && (
                  <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-[var(--danger)] border border-[var(--canvas)]"></span>
                )}
              </button>

              {notificationsOpen && (
                <div className="absolute right-0 mt-2 w-80 ui-dropdown z-50">
                  <div className="p-4 border-b border-[var(--line)] flex items-center justify-between">
                    <h4 className="font-semibold text-sm">Notifications</h4>
                    {notifications.length > 0 && (
                      <button 
                        onClick={() => setNotifications([])}
                        className="text-xs text-[var(--brand)] hover:underline cursor-pointer"
                      >
                        Mark all read
                      </button>
                    )}
                  </div>
                  <div className="p-2 space-y-1 max-h-64 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="p-4 text-center text-sm text-[var(--text-muted)]">No new notifications</div>
                    ) : (
                      notifications.map(notif => (
                        <div 
                          key={notif.id} 
                          onClick={() => setNotifications(notifications.filter(n => n.id !== notif.id))}
                          className="p-3 hover:bg-[var(--surface-raised)] rounded-lg cursor-pointer transition-colors"
                        >
                          <p className="text-sm text-[var(--text)]">{notif.message}</p>
                          <p className="text-xs text-[var(--text-muted)] mt-1">{notif.time}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="h-8 w-px bg-[var(--line)] mx-1 hidden sm:block"></div>

            <div className="relative hidden sm:block">
              <button
                className="flex items-center gap-3 text-left hover:bg-[var(--surface-raised)] p-2 rounded-lg transition-colors"
                onClick={() => { setProfileOpen(!profileOpen); setNotificationsOpen(false); }}
              >
                <div>
                  <p className="text-sm font-semibold text-[var(--text)]">{user?.name}</p>
                </div>
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--brand)] text-xs font-bold text-white">
                  {initials}
                </span>
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-48 ui-dropdown z-50 p-1">
                  <Link to="/profile" onClick={() => setProfileOpen(false)} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text)] hover:bg-[var(--surface-raised)] rounded-md transition-colors">
                    <User size={14} /> Profile
                  </Link>
                  <Link to="/settings" onClick={() => setProfileOpen(false)} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text)] hover:bg-[var(--surface-raised)] rounded-md transition-colors">
                    <Settings size={14} /> Settings
                  </Link>
                  <div className="h-px bg-[var(--line)] my-1"></div>
                  <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--danger)] hover:bg-[var(--danger-soft)] rounded-md transition-colors" onClick={signOut}>
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto pb-12" onClick={() => { setNotificationsOpen(false); setProfileOpen(false); }}>
          <div className="app-page">
            <div className="sm:hidden mb-6">
              <p className="text-kicker text-[var(--brand)]">{current.eyebrow}</p>
              <h1 className="text-2xl font-semibold tracking-tight text-[var(--text)] mt-1">{current.title}</h1>
            </div>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
