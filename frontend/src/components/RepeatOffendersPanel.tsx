import { Link } from 'react-router-dom';
import { AlertOctagon, ArrowRight } from 'lucide-react';
import { type RepeatOffenderItem } from '../api/dashboard';
import { EmptyState } from './ui';

/**
 * Surfaces brands that have FAILed compliance across 2+ separate
 * inspections. Each item already represents a merged, per-inspection
 * verdict (see DashboardService._compute_repeat_offenders on the backend) —
 * not a raw count of failed photos — so "3/5 failed" here genuinely means
 * 3 distinct market visits found this brand out of compliance.
 */
export default function RepeatOffendersPanel({ offenders }: { offenders: RepeatOffenderItem[] }) {
  if (!offenders.length) {
    return (
      <EmptyState
        icon={<AlertOctagon size={28} />}
        title="No repeat offenders yet"
        description="Brands that fail compliance on 2 or more separate inspections will be flagged here for follow-up or escalation."
      />
    );
  }

  return (
    <div className="divide-y divide-[var(--line-strong)]">
      {offenders.map((offender) => (
        <Link
          key={offender.brand}
          to={`/inspections/${offender.latest_inspection_id}`}
          className="group flex items-center justify-between gap-3 px-4 py-3.5 sm:px-6 sm:py-4 transition-colors hover:bg-[var(--surface)] border-l-4 border-[var(--danger)]"
        >
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <p className="truncate text-sm sm:text-base font-bold text-[var(--text)] group-hover:text-[var(--brand)] transition-colors">
                {offender.brand}
              </p>
              <span className="shrink-0 rounded-full bg-[var(--danger-soft)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--danger)]">
                {offender.fail_count}/{offender.total_inspections} failed
              </span>
            </div>
            {offender.top_violation_rule_id ? (
              <p className="mt-1 truncate text-xs sm:text-sm text-[var(--text-muted)]">
                Most common: <span className="font-mono text-[var(--brand)]">{offender.top_violation_rule_id}</span> {offender.top_violation_rule_name} ({offender.top_violation_count}x)
              </p>
            ) : (
              <p className="mt-1 truncate text-xs sm:text-sm text-[var(--text-muted)]">Latest: {offender.latest_inspection_number}</p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-4">
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[var(--surface-raised)] border border-[var(--line)] flex items-center justify-center group-hover:bg-[var(--brand)] group-hover:border-[var(--brand)] group-hover:text-white text-[var(--text-faint)] transition-all">
              <ArrowRight size={14} />
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
