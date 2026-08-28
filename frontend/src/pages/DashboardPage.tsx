import { useEffect, useState } from 'react';
import { ArrowRight, ClipboardList, FileSearch, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDashboardAnalytics, type DashboardAnalyticsResponse } from '../api/dashboard';
import ViolationChart from '../components/ViolationChart';
import { Alert, EmptyState, LoadingState, Metric, SectionHeader, StatusBadge } from '../components/ui';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  useEffect(() => { getDashboardAnalytics().then(setData).catch(() => setFailed(true)).finally(() => setLoading(false)); }, []);
  if (loading) return <LoadingState label="Preparing compliance operations overview" />;

  const kpis = data?.kpis;
  const openCases = (kpis?.review_count || 0) + (kpis?.not_analysed_count || 0);
  const ruleBreaches = data?.top_violations.reduce((total, item) => total + item.count, 0) || 0;
  return <div className="space-y-7">
    <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="app-kicker">Compliance operations</p><h2 className="app-title mt-2">Decision-ready inspection oversight.</h2><p className="app-subtitle mt-3">Monitor evidence-led cases, unresolved reviews, and rule outcomes from one operational workspace.</p></div><Link to="/inspections/new" className="ui-button-primary"><Plus size={16} /> New inspection</Link></section>
    {failed && <Alert tone="error">Dashboard data could not be loaded. You can continue working in the inspection register.</Alert>}
    <section className="grid overflow-hidden border border-[var(--line)] bg-[var(--surface)] sm:grid-cols-2 xl:grid-cols-4" aria-label="Operational metrics">
      <Metric label="Inspections" value={kpis?.total_inspections || 0} detail="Recorded in this workspace" tone="info" />
      <Metric label="Open cases" value={openCases} detail="Awaiting analysis or review" tone="review" />
      <Metric label="Compliance rate" value={`${kpis?.compliance_rate || 0}%`} detail="Across analysed inspections" tone="pass" />
      <Metric label="Rule breaches" value={ruleBreaches} detail="Across listed rule findings" tone="fail" />
    </section>
    <section className="grid gap-5 xl:grid-cols-[.95fr_1.05fr]">
      <article className="app-surface overflow-hidden"><SectionHeader eyebrow="Rule distribution" title="Frequent rule failures" description="The rule references occurring most often in recorded reports." action={<FileSearch size={18} className="text-[var(--text-faint)]" />} /><div className="p-5"><ViolationChart violations={data?.top_violations || []} /></div></article>
      <article className="app-surface overflow-hidden"><SectionHeader eyebrow="Case queue" title="Recent inspections" description="Latest evidence records in the current workspace." action={<Link to="/inspections" className="text-xs font-semibold text-[var(--brand)] hover:text-[var(--brand-hover)]">View register</Link>} />
        {data?.recent_inspections?.length ? <div className="divide-y divide-[var(--line)]">{data.recent_inspections.map((inspection) => <Link key={inspection.id} to={`/inspections/${inspection.id}`} className="group flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-[var(--surface-raised)]"><div className="min-w-0"><p className="truncate text-sm font-semibold text-[var(--text)]">{inspection.product_name}</p><p className="mt-1 truncate font-mono text-[11px] text-[var(--text-faint)]">{inspection.inspection_number} · {inspection.brand}</p></div><div className="flex shrink-0 items-center gap-3"><StatusBadge value={inspection.compliance_status} /><ArrowRight size={16} className="text-[var(--text-faint)] transition-colors group-hover:text-[var(--brand)]" /></div></Link>)}</div> : <EmptyState icon={<ClipboardList size={28} />} title="No inspections yet" description="Create an inspection to begin evidence-based compliance analysis." action={<Link to="/inspections/new" className="ui-button-primary">Create inspection</Link>} />}
      </article>
    </section>
  </div>;
}
