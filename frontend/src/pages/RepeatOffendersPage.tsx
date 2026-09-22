import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertOctagon,
  ArrowRight,
  ExternalLink,
  FileSearch,
  Search,
  ShieldAlert,
  X,
  Filter,
  Layers,
} from 'lucide-react';
import { getRepeatOffenders, type RepeatOffenderItem } from '../api/dashboard';
import { Alert, EmptyState, LoadingState, Metric } from '../components/ui';

export default function RepeatOffendersPage() {
  const [offenders, setOffenders] = useState<RepeatOffenderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState<'fails_desc' | 'total_desc' | 'brand_asc' | 'date_desc'>('fails_desc');

  useEffect(() => {
    getRepeatOffenders()
      .then(setOffenders)
      .catch(() => setFailed(true))
      .finally(() => setLoading(false));
  }, []);

  // Filter & sort
  const filteredAndSorted = useMemo(() => {
    const q = query.trim().toLowerCase();
    let list = offenders.filter((item) => {
      if (!q) return true;
      return (
        item.brand.toLowerCase().includes(q) ||
        (item.top_violation_rule_id && item.top_violation_rule_id.toLowerCase().includes(q)) ||
        (item.top_violation_rule_name && item.top_violation_rule_name.toLowerCase().includes(q)) ||
        item.latest_inspection_number.toLowerCase().includes(q)
      );
    });

    return list.sort((a, b) => {
      if (sortBy === 'fails_desc') {
        if (b.fail_count !== a.fail_count) return b.fail_count - a.fail_count;
        return b.total_inspections - a.total_inspections;
      }
      if (sortBy === 'total_desc') {
        return b.total_inspections - a.total_inspections;
      }
      if (sortBy === 'brand_asc') {
        return a.brand.localeCompare(b.brand);
      }
      if (sortBy === 'date_desc') {
        return new Date(b.latest_inspection_date).getTime() - new Date(a.latest_inspection_date).getTime();
      }
      return 0;
    });
  }, [offenders, query, sortBy]);

  // Summary calculations
  const totalOffenders = offenders.length;
  const totalFailedCases = offenders.reduce((sum, item) => sum + item.fail_count, 0);

  // Determine top common rule across all offenders
  const topRule = useMemo(() => {
    const counts: Record<string, { id: string; name: string; count: number }> = {};
    for (const item of offenders) {
      if (item.top_violation_rule_id && item.top_violation_rule_name) {
        if (!counts[item.top_violation_rule_id]) {
          counts[item.top_violation_rule_id] = {
            id: item.top_violation_rule_id,
            name: item.top_violation_rule_name,
            count: 0,
          };
        }
        counts[item.top_violation_rule_id].count += item.top_violation_count;
      }
    }
    const sortedRules = Object.values(counts).sort((a, b) => b.count - a.count);
    return sortedRules[0] || null;
  }, [offenders]);

  if (loading) {
    return <LoadingState label="Auditing brand violation records for repeat offenders" />;
  }

  return (
    <div className="space-y-6 sm:space-y-8 max-w-[1920px] mx-auto">
      {/* Header section */}
      <section className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="heading-page flex items-center gap-2.5">
            <span className="p-1.5 rounded-lg bg-[var(--danger-soft)] text-[var(--danger)]">
              <ShieldAlert size={24} />
            </span>
            Repeat offenders
          </h2>
          <p className="text-body mt-1 text-xs sm:text-sm max-w-3xl">
            Manufacturers and brands that have failed compliance on 2 or more distinct inspections.
            These patterns warrant formal notices, targeted market audits, or legal scrutiny rather than one-off corrections.
          </p>
        </div>
        <Link
          to="/inspections"
          className="neo-button-secondary whitespace-nowrap w-full sm:w-auto justify-center shadow-sm"
        >
          View all inspections
        </Link>
      </section>

      {failed && (
        <Alert tone="error">
          Repeat offenders data could not be loaded. Please check the backend connection and try again.
        </Alert>
      )}

      {/* KPI Metrics */}
      <section className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4" aria-label="Escalation metrics">
        <Metric
          label="Flagged Brands"
          value={totalOffenders}
          detail="Brands with ≥2 failed inspections"
          tone="fail"
        />
        <Metric
          label="Total Failed Inspections"
          value={totalFailedCases}
          detail="Across repeat offender brands"
          tone="fail"
        />
        <Metric
          label="Primary Violation"
          value={topRule ? topRule.id : 'None'}
          detail={topRule ? `${topRule.name} (${topRule.count}x)` : 'No repeat violations'}
          tone="info"
        />
        <Metric
          label="Escalation Threshold"
          value="≥ 2 Fails"
          detail="Separate market visits required"
          tone="review"
        />
      </section>

      {/* Search & Sort Controls */}
      <section className="depth-1 p-3.5 sm:p-4 rounded-xl border border-[var(--line)]">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1 min-w-0">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" />
            <input
              className="neo-input pl-10 pr-9 !min-h-[42px] h-10 text-xs sm:text-sm"
              placeholder="Search by brand name, violation rule, or inspection ID"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-faint)] hover:text-[var(--text)]"
                aria-label="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-2 bg-[var(--surface-raised)] border border-[var(--line)] rounded-lg text-xs text-[var(--text-muted)] shrink-0">
              <Filter size={14} />
              <span className="font-semibold">Sort:</span>
            </div>
            <select
              className="neo-select !min-h-[42px] h-10 text-xs sm:text-sm flex-1 sm:w-auto sm:min-w-[170px]"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              aria-label="Sort repeat offenders"
            >
              <option value="fails_desc">Most failures</option>
              <option value="total_desc">Most total inspections</option>
              <option value="brand_asc">Brand name (A-Z)</option>
              <option value="date_desc">Most recent incident</option>
            </select>
          </div>
        </div>
      </section>

      {/* Main Offenders Content */}
      {offenders.length === 0 ? (
        <EmptyState
          icon={<AlertOctagon size={36} />}
          title="No repeat offenders yet"
          description="Brands that fail compliance on 2 or more separate inspections across this workspace will be automatically flagged here for follow-up and escalation."
          action={
            <Link to="/inspections/new" className="neo-button-primary mt-4 w-full sm:w-auto">
              Create inspection
            </Link>
          }
        />
      ) : filteredAndSorted.length === 0 ? (
        <EmptyState
          icon={<FileSearch size={32} />}
          title="No matching repeat offenders"
          description={`No flagged brands matching "${query}" were found.`}
          action={
            <button
              type="button"
              onClick={() => setQuery('')}
              className="neo-button-secondary mt-4 w-full sm:w-auto"
            >
              Clear search filter
            </button>
          }
        />
      ) : (
        <div className="space-y-4">
          <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
            {filteredAndSorted.map((offender) => {
              const failRate = Math.round((offender.fail_count / offender.total_inspections) * 100);
              const formattedDate = new Date(offender.latest_inspection_date).toLocaleDateString(undefined, {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              });

              return (
                <article
                  key={offender.brand}
                  className="depth-2 rounded-xl p-5 sm:p-6 border border-[var(--line-strong)] border-l-4 border-l-[var(--danger)] flex flex-col justify-between gap-5 bg-[var(--surface)] hover:bg-[var(--surface-pale)] transition-colors"
                >
                  {/* Card Header */}
                  <div>
                    <div className="flex flex-wrap items-start justify-between gap-3 mb-2">
                      <div className="min-w-0 flex-1">
                        <h3 className="text-base sm:text-lg font-bold text-[var(--text)] truncate">
                          {offender.brand}
                        </h3>
                        <p className="text-xs text-[var(--text-muted)] mt-0.5">
                          {offender.total_inspections} total inspection{offender.total_inspections === 1 ? '' : 's'} recorded
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="inline-flex items-center gap-1 rounded-full bg-[var(--danger-soft)] px-2.5 py-1 text-xs font-bold text-[var(--danger)]">
                          <AlertOctagon size={13} />
                          {offender.fail_count} / {offender.total_inspections} Failed ({failRate}%)
                        </span>
                      </div>
                    </div>

                    {/* Failure Progress Bar */}
                    <div className="w-full bg-[var(--surface-raised)] h-2 rounded-full overflow-hidden my-3 border border-[var(--line)]">
                      <div
                        className="bg-[var(--danger)] h-full transition-all duration-500 rounded-full"
                        style={{ width: `${Math.min(100, Math.max(10, failRate))}%` }}
                      />
                    </div>

                    {/* Breakdown details */}
                    <div className="space-y-2.5 pt-1 text-xs sm:text-sm">
                      {offender.top_violation_rule_id && (
                        <div className="p-3 bg-[var(--canvas)] rounded-lg border border-[var(--line-strong)]">
                          <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] mb-1">
                            Most Repeated Violation
                          </p>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs font-bold text-[var(--brand)] px-2 py-0.5 bg-[var(--brand-soft)] rounded">
                              {offender.top_violation_rule_id}
                            </span>
                            <span className="font-semibold text-[var(--text)]">
                              {offender.top_violation_rule_name}
                            </span>
                            <span className="text-xs font-bold text-[var(--danger)] ml-auto">
                              {offender.top_violation_count}x detected
                            </span>
                          </div>
                        </div>
                      )}

                      <div className="flex flex-wrap items-center justify-between text-xs text-[var(--text-muted)] px-1 pt-1">
                        <span>
                          Latest inspection:{' '}
                          <Link
                            to={`/inspections/${offender.latest_inspection_id}`}
                            className="font-mono font-bold text-[var(--brand)] hover:underline inline-flex items-center gap-1"
                          >
                            {offender.latest_inspection_number}
                            <ExternalLink size={12} />
                          </Link>
                        </span>
                        <span className="font-mono text-[var(--text-faint)]">{formattedDate}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions Footer */}
                  <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-[var(--line)]">
                    <Link
                      to={`/inspections?search=${encodeURIComponent(offender.brand)}`}
                      className="neo-button-secondary text-xs flex-1 justify-center !min-h-[36px] h-9"
                    >
                      <Layers size={14} /> Filter brand inspections
                    </Link>
                    <Link
                      to={`/inspections/${offender.latest_inspection_id}`}
                      className="neo-button-primary text-xs flex-1 justify-center !min-h-[36px] h-9"
                    >
                      View latest inspection <ArrowRight size={14} />
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
