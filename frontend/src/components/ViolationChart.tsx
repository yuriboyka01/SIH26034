import { type ViolationSummaryItem } from '../api/dashboard';
import { EmptyState } from './ui';

export default function ViolationChart({ violations }: { violations: ViolationSummaryItem[] }) {
  if (!violations.length) return <EmptyState icon={<span className="text-2xl">—</span>} title="No rule failures recorded" description="Failure distribution will appear after compliance reports are available." />;
  const max = Math.max(...violations.map(({ count }) => count));
  return <div className="space-y-5">{violations.map((violation) => {
    const percentage = Math.max((violation.count / max) * 100, 3);
    return <div key={violation.rule_id}><div className="mb-2 flex items-baseline justify-between gap-4"><div className="min-w-0"><p className="font-mono text-[11px] font-bold text-[var(--brand)]">{violation.rule_id}</p><p className="mt-0.5 truncate text-sm text-[var(--text-muted)]">{violation.rule_name}</p></div><span className="font-mono text-sm font-semibold text-[var(--text)]">{violation.count}</span></div><div className="h-1.5 overflow-hidden bg-[var(--line)]"><div className="h-full bg-[var(--danger)]" style={{ width: `${percentage}%` }} /></div></div>;
  })}</div>;
}
