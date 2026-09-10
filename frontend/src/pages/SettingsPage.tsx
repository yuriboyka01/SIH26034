export default function SettingsPage() {
  return (
    <div className="max-w-2xl">
      <div className="bg-[var(--surface)] rounded-xl shadow-sm border border-[var(--line)] overflow-hidden">
        <div className="p-6 sm:p-8">
          <h2 className="text-2xl font-semibold text-[var(--text)] mb-6">Settings</h2>
          
          <div className="space-y-6">
            <div className="pb-6 border-b border-[var(--line)]">
              <h3 className="text-lg font-medium text-[var(--text)] mb-2">Preferences</h3>
              <p className="text-sm text-[var(--text-muted)] mb-4">Manage your workspace preferences.</p>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-[var(--text)]">Email Notifications</p>
                    <p className="text-xs text-[var(--text-muted)]">Receive daily summaries of your inspections.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" value="" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[var(--brand)]"></div>
                  </label>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-[var(--text)] mb-2">Security</h3>
              <p className="text-sm text-[var(--text-muted)] mb-4">Manage your security settings.</p>
              <button className="px-4 py-2 bg-[var(--surface-raised)] border border-[var(--line)] text-sm font-medium text-[var(--text)] rounded-lg hover:bg-[var(--surface-hover)] transition-colors">
                Change Password
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
