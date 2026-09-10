import { useEffect, useState } from 'react';
import { ArrowRight, ClipboardList, FileSearch, Plus, Box, Search, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDashboardAnalytics, type DashboardAnalyticsResponse } from '../api/dashboard';
import ViolationChart from '../components/ViolationChart';
import { Alert, EmptyState, LoadingState, Metric, SectionHeader, StatusBadge } from '../components/ui';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    getDashboardAnalytics()
      .then(setData)
      .catch(() => setFailed(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState label="Preparing compliance operations overview" />;

  const kpis = data?.kpis;
  const openCases = (kpis?.review_count || 0) + (kpis?.not_analysed_count || 0);
  const ruleBreaches = data?.top_violations.reduce((total, item) => total + item.count, 0) || 0;
  const q = query.toLowerCase();

  return (
    <div className="space-y-8 max-w-[1920px] mx-auto">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <p className="text-sm text-[var(--text-muted)] max-w-2xl">
          Evidence-led cases, unresolved reviews, and rule outcomes for this workspace.
        </p>
        <Link to="/inspections/new" className="neo-button-primary whitespace-nowrap">
          <Plus size={18} /> New inspection
        </Link>
      </section>

      {failed && <Alert tone="error">Dashboard data could not be loaded. You can continue working in the inspection register.</Alert>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Operational metrics">
        <Metric label="Total Inspections" value={kpis?.total_inspections || 0} detail="Recorded in this workspace" tone="info" />
        <Metric label="Open Cases" value={openCases} detail="Awaiting analysis or review" tone="review" />
        <Metric label="Compliance Rate" value={`${kpis?.compliance_rate || 0}%`} detail="Across analysed inspections" tone="pass" />
        <Metric label="Rule Breaches" value={ruleBreaches} detail="Across listed rule findings" tone="fail" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">
        <article className="depth-2 flex flex-col">
          <SectionHeader
            eyebrow="Analytics"
            title="Frequent rule failures"
            description="The rule references occurring most often in recorded reports."
            action={<div className="w-10 h-10 bg-[var(--surface-raised)] border border-[var(--line)] rounded-full flex items-center justify-center"><FileSearch size={18} className="text-[var(--text-muted)]" /></div>}
          />
          <div className="p-6 flex-1 flex flex-col justify-center bg-[var(--canvas)] m-4 rounded-xl border border-[var(--line-strong)]">
            <ViolationChart violations={data?.top_violations || []} />
          </div>
        </article>

        <article className="depth-2 flex flex-col">
          <div className="flex items-start justify-between gap-4 px-6 py-5 border-b border-[var(--line)] bg-[var(--surface)]/50 backdrop-blur-sm">
            <div>
              <p className="text-kicker mb-1.5">Case Queue</p>
              <h3 className="heading-section">Recent inspections</h3>
            </div>
            <Link to="/inspections" className="text-sm font-bold text-[var(--brand)] hover:text-[var(--brand-hover)] bg-[var(--brand-soft)] px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap">
              View register
            </Link>
          </div>

          <div className="px-6 py-3 border-b border-[var(--line)] bg-[var(--surface)]/50">
            <div className="relative max-w-xs">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Filter recent inspections"
                className="neo-input pl-9 pr-8 h-9 text-sm bg-[var(--surface-pale)] border-[var(--line)]"
              />
              {query && (
                <button type="button" onClick={() => setQuery('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)] hover:text-[var(--text)]" aria-label="Clear filter">
                  <X size={14} />
                </button>
              )}
            </div>
          </div>

          <div className="flex-1 bg-[var(--surface-pale)]">
            {data?.recent_inspections?.length ? (() => {
              const filteredInspections = data.recent_inspections.filter(
                (inspection) =>
                  inspection.product_name.toLowerCase().includes(q) ||
                  inspection.inspection_number.toLowerCase().includes(q) ||
                  inspection.brand.toLowerCase().includes(q)
              );

              if (filteredInspections.length === 0) {
                return (
                  <div className="p-8">
                    <EmptyState
                      icon={<FileSearch size={32} />}
                      title="No matches found"
                      description={`No inspections matching "${query}" were found in recent records.`}
                    />
                  </div>
                );
              }

              return (
                <div className="divide-y divide-[var(--line-strong)]">
                  {filteredInspections.map((inspection) => (
                  <Link key={inspection.id} to={`/inspections/${inspection.id}`} className="group flex items-center justify-between gap-4 px-6 py-4 transition-colors hover:bg-[var(--surface)] border-l-4 border-transparent hover:border-[var(--brand)]">
                    <div className="min-w-0">
                      <p className="truncate text-base font-bold text-[var(--text)] group-hover:text-[var(--brand)] transition-colors">{inspection.product_name}</p>
                      <p className="mt-1.5 flex items-center gap-2 truncate font-mono text-[11px] font-semibold text-[var(--text-faint)] tracking-wide">
                        <span className="text-[var(--brand)]">{inspection.inspection_number}</span>
                        <span className="flex items-center gap-1"><Box size={12}/> {inspection.brand}</span>
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-4">
                      <StatusBadge value={inspection.compliance_status} />
                      <div className="w-8 h-8 rounded-full bg-[var(--surface-raised)] border border-[var(--line)] flex items-center justify-center group-hover:bg-[var(--brand)] group-hover:border-[var(--brand)] group-hover:text-white text-[var(--text-faint)] transition-all">
                        <ArrowRight size={14} />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
              );
            })() : (
              <div className="p-8">
                <EmptyState
                  icon={<ClipboardList size={32} />}
                  title="No inspections yet"
                  description="Create an inspection to begin evidence-based compliance analysis."
                  action={<Link to="/inspections/new" className="neo-button-primary mt-4">Create inspection</Link>}
                />
              </div>
            )}
          </div>
        </article>
      </section>
    </div>
  );
}
