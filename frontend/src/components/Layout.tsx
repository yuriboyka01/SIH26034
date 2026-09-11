import { Outlet, NavLink, Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { ClipboardList, LayoutDashboard, LogOut, Menu, Plus, X, Bell, Moon, Sun, Settings, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const mainNavigation = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/inspections', label: 'Inspections', icon: ClipboardList },
];

const accountNavigation = [
  { to: '/profile', label: 'Profile', icon: User },
  { to: '/settings', label: 'Settings', icon: Settings },
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

  const signOut = () => { 
    setMobileOpen(false);
    logout(); 
    navigate('/login'); 
  };

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [darkMode]);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileOpen(false);
    setNotificationsOpen(false);
    setProfileOpen(false);
  }, [location.pathname]);

  const navigationContent = (
    <div className="flex flex-col h-full">
      <div className={`flex h-16 lg:h-20 items-center gap-3 border-b border-[var(--sidebar-line)] shrink-0 ${desktopCollapsed ? 'justify-center px-0' : 'px-5 sm:px-6'}`}>
        <img src="/logo.jpeg" alt="COMPLIQ Logo" className="h-8 w-8 lg:h-9 lg:w-9 rounded-lg bg-white object-contain p-1 shrink-0" />
        {!desktopCollapsed && (
          <div className="overflow-hidden transition-all duration-300 whitespace-nowrap min-w-0">
            <p className="text-sm font-bold tracking-[.15em] text-[var(--sidebar-text)]">COMPLIQ</p>
            <p className="text-[10px] uppercase tracking-wider text-[var(--sidebar-text-faint)] truncate">Compliance Workspace</p>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto py-5 no-scrollbar">
        <div className={`mb-5 ${desktopCollapsed ? 'px-2' : 'px-4'}`}>
          <NavLink
            to="/inspections/new"
            onClick={() => setMobileOpen(false)}
            title={desktopCollapsed ? "New inspection" : undefined}
            className={`flex items-center justify-center gap-2 rounded-lg bg-[var(--brand)] py-2.5 lg:py-3 text-sm font-semibold text-white transition-colors hover:bg-[var(--brand-hover)] w-full shadow-md ${desktopCollapsed ? 'px-0' : 'px-4'}`}
          >
            <Plus size={18} className={desktopCollapsed ? '' : 'shrink-0'} /> {!desktopCollapsed && "New inspection"}
          </NavLink>
        </div>

        {!desktopCollapsed && (
          <div className="px-4 mb-2 mt-1">
            <p className="px-2 text-[10px] font-bold uppercase tracking-[.15em] text-[var(--sidebar-text-faint)]">Workspace</p>
          </div>
        )}

        <nav className={`space-y-1 ${desktopCollapsed ? 'px-2' : 'px-3'}`} aria-label="Primary navigation">
          {mainNavigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              title={desktopCollapsed ? label : undefined}
              className={({ isActive }) => `
                group flex items-center gap-3 rounded-lg py-2.5 text-sm font-medium transition-colors duration-200 border-l-2
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

        {/* Account links visible in mobile drawer or when expanded */}
        <div className="mt-6 pt-5 border-t border-[var(--sidebar-line)] lg:hidden">
          <div className="px-4 mb-2">
            <p className="px-2 text-[10px] font-bold uppercase tracking-[.15em] text-[var(--sidebar-text-faint)]">Account</p>
          </div>
          <nav className="space-y-1 px-3" aria-label="Account navigation">
            {accountNavigation.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) => `
                  group flex items-center gap-3 rounded-lg py-2.5 px-3 text-sm font-medium transition-colors duration-200 border-l-2
                  ${isActive
                    ? 'border-[var(--brand)] bg-[var(--sidebar-surface)] text-white'
                    : 'border-transparent text-[var(--sidebar-text-muted)] hover:bg-[var(--sidebar-surface)] hover:text-white'
                  }
                `}
              >
                {({ isActive }) => (
                  <>
                    <Icon size={18} className={isActive ? 'text-white' : 'text-[var(--sidebar-text-muted)] group-hover:text-white transition-colors'} />
                    {label}
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      <div className={`border-t border-[var(--sidebar-line)] shrink-0 ${desktopCollapsed ? 'p-2' : 'p-4'}`}>
        {!desktopCollapsed && (
          <div className="mb-3 flex items-center gap-3 px-2">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--brand)] text-xs font-bold text-white">
              {initials}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-[var(--sidebar-text)]">{user?.name || 'Inspector'}</p>
              <p className="truncate text-[11px] text-[var(--sidebar-text-faint)]">{user?.email || ''}</p>
            </div>
          </div>
        )}
        <button
          className={`flex w-full items-center gap-2 rounded-lg py-2 text-sm font-medium text-[var(--danger-text)] transition-colors hover:bg-white/5 hover:text-white ${desktopCollapsed ? 'justify-center px-0' : 'px-3'}`}
          onClick={signOut}
          title={desktopCollapsed ? "Sign out" : undefined}
        >
          <LogOut size={16} /> {!desktopCollapsed && "Sign out"}
        </button>
      </div>
    </div>
  );

  return (
    <div className="app-shell flex bg-[var(--canvas)] transition-colors duration-300">
      {/* Desktop Sidebar */}
      <aside className={`sticky top-0 hidden h-[100dvh] shrink-0 flex-col bg-[var(--sidebar-bg)] lg:flex z-40 transition-all duration-300 ease-in-out ${desktopCollapsed ? 'w-20' : 'w-64'}`}>
        {navigationContent}
      </aside>

      {/* Mobile Sidebar Backdrop */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 z-40 bg-[var(--sidebar-bg)]/80 backdrop-blur-sm lg:hidden transition-opacity duration-300"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}
      
      {/* Mobile Sidebar Drawer */}
      <aside 
        className={`fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col bg-[var(--sidebar-bg)] shadow-2xl transition-transform duration-300 ease-out lg:hidden ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`} 
        aria-label="Mobile navigation"
      >
        {navigationContent}
      </aside>

      {/* Main Content Area */}
      <div className="min-w-0 flex-1 flex flex-col h-[100dvh] overflow-hidden">

        {/* Top Navigation Layer */}
        <header className="sticky top-0 z-30 flex h-16 lg:h-20 shrink-0 items-center justify-between border-b border-[var(--line)] bg-[var(--canvas)]/90 backdrop-blur-md px-3 sm:px-6 lg:px-10 transition-colors duration-300">
          <div className="flex items-center gap-3 min-w-0">
            <button 
              className="ui-icon-button shrink-0" 
              onClick={() => {
                if (window.innerWidth >= 1024) setDesktopCollapsed(!desktopCollapsed);
                else setMobileOpen(!mobileOpen);
              }} 
              aria-label="Toggle navigation"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            
            <div className="min-w-0">
              <p className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-[var(--brand)] truncate">{current.eyebrow}</p>
              <h1 className="text-sm sm:text-lg lg:text-xl font-semibold tracking-tight text-[var(--text)] truncate">{current.title}</h1>
            </div>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
            <button 
              className="ui-icon-button" 
              onClick={() => setDarkMode(!darkMode)} 
              title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
              aria-label="Toggle theme"
            >
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <div className="relative">
              <button 
                className="ui-icon-button relative" 
                onClick={() => { setNotificationsOpen(!notificationsOpen); setProfileOpen(false); }}
                aria-label="Notifications"
              >
                <Bell size={18} />
                {notifications.length > 0 && (
                  <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-[var(--danger)] border border-[var(--canvas)]" />
                )}
              </button>

              {notificationsOpen && (
                <div className="absolute right-0 mt-2 w-[calc(100vw-2rem)] max-w-xs sm:w-80 ui-dropdown z-50">
                  <div className="p-3.5 sm:p-4 border-b border-[var(--line)] flex items-center justify-between">
                    <h4 className="font-semibold text-sm text-[var(--text)]">Notifications</h4>
                    {notifications.length > 0 && (
                      <button 
                        onClick={() => setNotifications([])}
                        className="text-xs font-medium text-[var(--brand)] hover:underline cursor-pointer"
                      >
                        Mark all read
                      </button>
                    )}
                  </div>
                  <div className="p-2 space-y-1 max-h-64 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="p-4 text-center text-xs sm:text-sm text-[var(--text-muted)]">No new notifications</div>
                    ) : (
                      notifications.map(notif => (
                        <div 
                          key={notif.id} 
                          onClick={() => setNotifications(notifications.filter(n => n.id !== notif.id))}
                          className="p-3 hover:bg-[var(--surface-raised)] rounded-lg cursor-pointer transition-colors"
                        >
                          <p className="text-xs sm:text-sm text-[var(--text)]">{notif.message}</p>
                          <p className="text-[10px] sm:text-xs text-[var(--text-muted)] mt-1">{notif.time}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="h-6 w-px bg-[var(--line)] mx-1 hidden sm:block" />

            <div className="relative hidden sm:block">
              <button
                className="flex items-center gap-2.5 text-left hover:bg-[var(--surface-raised)] p-1.5 rounded-lg transition-colors"
                onClick={() => { setProfileOpen(!profileOpen); setNotificationsOpen(false); }}
                aria-label="User account"
              >
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--brand)] text-xs font-bold text-white">
                  {initials}
                </span>
                <p className="text-sm font-semibold text-[var(--text)] max-w-[120px] truncate">{user?.name || 'User'}</p>
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-48 ui-dropdown z-50 p-1">
                  <Link to="/profile" onClick={() => setProfileOpen(false)} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text)] hover:bg-[var(--surface-raised)] rounded-md transition-colors">
                    <User size={14} /> Profile
                  </Link>
                  <Link to="/settings" onClick={() => setProfileOpen(false)} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text)] hover:bg-[var(--surface-raised)] rounded-md transition-colors">
                    <Settings size={14} /> Settings
                  </Link>
                  <div className="h-px bg-[var(--line)] my-1" />
                  <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--danger)] hover:bg-[var(--danger-soft)] rounded-md transition-colors" onClick={signOut}>
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto pb-12 overflow-x-hidden" onClick={() => { setNotificationsOpen(false); setProfileOpen(false); }}>
          <div className="app-page">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
