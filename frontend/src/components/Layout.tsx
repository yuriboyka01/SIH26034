import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { ClipboardList, LayoutDashboard, LogOut, Menu, Plus, ShieldCheck, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navigation = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/inspections', label: 'Inspections', icon: ClipboardList },
];

const pageTitles: Record<string, { eyebrow: string; title: string }> = {
  '/dashboard': { eyebrow: 'Compliance workspace', title: 'Operations overview' },
  '/inspections': { eyebrow: 'Inspection register', title: 'Inspection records' },
  '/inspections/new': { eyebrow: 'Case intake', title: 'Create inspection' },
};

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const current = pageTitles[location.pathname] ?? { eyebrow: 'Evidence-led assessment', title: 'Inspection workspace' };
  const initials = user?.name?.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() || '?';
  const signOut = () => { logout(); navigate('/login'); };

  const navigationContent = <>
    <div className="border-b border-[var(--line)] px-5 py-5">
      <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-md border border-[#34415a] bg-[#111a2a] text-[#a9c7ff]"><ShieldCheck size={18} /></span><div><p className="text-sm font-bold tracking-[.1em] text-[var(--text)]">SIH26034</p><p className="mt-0.5 text-[11px] text-[var(--text-faint)]">Compliance Workspace</p></div></div>
    </div>
    <nav className="flex-1 px-3 py-5" aria-label="Primary navigation">
      <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[.14em] text-[var(--text-faint)]">Workspace</p>
      <div className="space-y-1">{navigation.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} onClick={() => setMobileOpen(false)} className={({ isActive }) => `flex items-center gap-3 rounded-md border px-3 py-2.5 text-sm font-medium transition-colors ${isActive ? 'border-[#3a4e79] bg-[#131d30] text-[#c5d8ff]' : 'border-transparent text-[var(--text-muted)] hover:bg-[var(--surface-raised)] hover:text-[var(--text)]'}`}><Icon size={17} />{label}</NavLink>)}</div>
      <NavLink to="/inspections/new" onClick={() => setMobileOpen(false)} className="ui-button-primary mt-5 w-full"><Plus size={16} /> New inspection</NavLink>
    </nav>
    <div className="border-t border-[var(--line)] p-4"><div className="mb-3 flex items-center gap-2.5 px-1"><span className="grid h-8 w-8 place-items-center rounded-full bg-[#1a2435] text-xs font-bold text-[#dbe5f4]">{initials}</span><div className="min-w-0"><p className="truncate text-sm font-medium text-[var(--text)]">{user?.name}</p><p className="truncate text-[11px] uppercase tracking-wide text-[var(--text-faint)]">{user?.role}</p></div></div><button className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-[var(--text-muted)] transition-colors hover:bg-[#24161b] hover:text-[#ffb4b4]" onClick={signOut}><LogOut size={16} /> Sign out</button></div>
  </>;

  return <div className="app-shell flex">
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-[var(--line)] bg-[var(--surface)] lg:flex">{navigationContent}</aside>
    {mobileOpen && <button className="fixed inset-0 z-40 bg-black/70 lg:hidden" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <aside className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-[var(--line)] bg-[var(--surface)] transition-transform duration-200 lg:hidden ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`} aria-label="Mobile navigation">{navigationContent}</aside>
    <div className="min-w-0 flex-1"><header className="sticky top-0 z-30 flex min-h-[72px] items-center justify-between border-b border-[var(--line)] bg-[var(--canvas)] px-4 lg:px-8"><div className="flex min-w-0 items-center gap-3"><button className="ui-icon-button lg:hidden" onClick={() => setMobileOpen((open) => !open)} aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'}>{mobileOpen ? <X size={20} /> : <Menu size={20} />}</button><div className="min-w-0"><p className="truncate text-[10px] font-bold uppercase tracking-[.13em] text-[var(--text-faint)]">{current.eyebrow}</p><h1 className="truncate text-base font-semibold tracking-tight text-[var(--text)] sm:text-lg">{current.title}</h1></div></div><span className="hidden border-l border-[var(--line)] pl-4 text-xs text-[var(--text-muted)] sm:inline">{user?.role || 'Inspector'}</span></header><main><div className="app-page"><Outlet /></div></main></div>
  </div>;
}
