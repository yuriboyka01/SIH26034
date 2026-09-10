import { useAuth } from '../context/AuthContext';

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="max-w-2xl">
      <div className="bg-[var(--surface)] rounded-xl shadow-sm border border-[var(--line)] overflow-hidden">
        <div className="p-6 sm:p-8">
          <div className="flex items-center gap-6 mb-8">
            <div className="h-20 w-20 rounded-full bg-[var(--brand)] flex items-center justify-center text-white text-2xl font-bold shrink-0">
              {user?.name?.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() || 'U'}
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-[var(--text)]">{user?.name || 'User'}</h2>
              <p className="text-sm text-[var(--text-muted)] mt-1">{user?.email}</p>
              <span className="inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--brand-soft)] text-[var(--brand)]">
                {user?.role || 'User'}
              </span>
            </div>
          </div>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-[var(--text)] mb-4">Account Information</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-[var(--surface-raised)] p-4 rounded-lg">
                  <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">Full Name</p>
                  <p className="font-medium text-[var(--text)]">{user?.name || 'Not set'}</p>
                </div>
                <div className="bg-[var(--surface-raised)] p-4 rounded-lg">
                  <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">Email Address</p>
                  <p className="font-medium text-[var(--text)]">{user?.email}</p>
                </div>
                <div className="bg-[var(--surface-raised)] p-4 rounded-lg">
                  <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">Role</p>
                  <p className="font-medium text-[var(--text)]">{user?.role || 'Not assigned'}</p>
                </div>
                <div className="bg-[var(--surface-raised)] p-4 rounded-lg">
                  <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">Member Since</p>
                  <p className="font-medium text-[var(--text)]">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
