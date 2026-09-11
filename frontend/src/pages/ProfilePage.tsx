import { useAuth } from '../context/AuthContext';
import { User, Mail, Shield, Calendar } from 'lucide-react';

export default function ProfilePage() {
  const { user } = useAuth();
  const initials = user?.name?.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() || 'U';

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="bg-[var(--surface)] rounded-xl shadow-sm border border-[var(--line)] overflow-hidden">
        <div className="p-5 sm:p-8">
          <div className="flex flex-col sm:flex-row items-center sm:items-start text-center sm:text-left gap-4 sm:gap-6 mb-6 sm:mb-8 pb-6 border-b border-[var(--line)]">
            <div className="h-16 w-16 sm:h-20 sm:w-20 rounded-full bg-[var(--brand)] flex items-center justify-center text-white text-xl sm:text-2xl font-bold shrink-0 shadow-md">
              {initials}
            </div>
            <div className="min-w-0">
              <h2 className="text-xl sm:text-2xl font-semibold text-[var(--text)]">{user?.name || 'Inspector'}</h2>
              <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-0.5">{user?.email}</p>
              <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--brand-soft)] text-[var(--brand)]">
                {user?.role || 'Inspector / Officer'}
              </span>
            </div>
          </div>
          
          <div className="space-y-5">
            <h3 className="text-sm sm:text-base font-bold text-[var(--text)] uppercase tracking-wider text-[11px] text-[var(--text-faint)]">Account Information</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div className="bg-[var(--surface-raised)] p-3.5 sm:p-4 rounded-lg border border-[var(--line)]">
                <p className="text-[10px] sm:text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <User size={13} className="text-[var(--brand)]" /> Full Name
                </p>
                <p className="font-semibold text-sm sm:text-base text-[var(--text)]">{user?.name || 'Not set'}</p>
              </div>
              <div className="bg-[var(--surface-raised)] p-3.5 sm:p-4 rounded-lg border border-[var(--line)]">
                <p className="text-[10px] sm:text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Mail size={13} className="text-[var(--brand)]" /> Email Address
                </p>
                <p className="font-semibold text-sm sm:text-base text-[var(--text)] truncate">{user?.email}</p>
              </div>
              <div className="bg-[var(--surface-raised)] p-3.5 sm:p-4 rounded-lg border border-[var(--line)]">
                <p className="text-[10px] sm:text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Shield size={13} className="text-[var(--brand)]" /> Role
                </p>
                <p className="font-semibold text-sm sm:text-base text-[var(--text)]">{user?.role || 'Inspector'}</p>
              </div>
              <div className="bg-[var(--surface-raised)] p-3.5 sm:p-4 rounded-lg border border-[var(--line)]">
                <p className="text-[10px] sm:text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Calendar size={13} className="text-[var(--brand)]" /> Member Since
                </p>
                <p className="font-semibold text-sm sm:text-base text-[var(--text)]">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Active'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
