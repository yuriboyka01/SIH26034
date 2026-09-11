export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-[var(--surface)] rounded-xl shadow-sm border border-[var(--line)] overflow-hidden">
        <div className="p-5 sm:p-8">
          <h2 className="text-xl sm:text-2xl font-semibold text-[var(--text)] mb-6">Settings</h2>
          
          <div className="space-y-6">
            <div className="pb-6 border-b border-[var(--line)]">
              <h3 className="text-base sm:text-lg font-medium text-[var(--text)] mb-1">Preferences</h3>
              <p className="text-xs sm:text-sm text-[var(--text-muted)] mb-4">Manage your workspace preferences.</p>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium text-sm sm:text-base text-[var(--text)]">Email Notifications</p>
                    <p className="text-xs text-[var(--text-muted)]">Receive daily summaries of your inspections.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer shrink-0">
                    <input type="checkbox" value="" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[var(--brand)]"></div>
                  </label>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-base sm:text-lg font-medium text-[var(--text)] mb-1">Security</h3>
              <p className="text-xs sm:text-sm text-[var(--text-muted)] mb-4">Manage your account authentication and password.</p>
              <button className="neo-button-secondary text-xs sm:text-sm w-full sm:w-auto justify-center">
                Change Password
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
