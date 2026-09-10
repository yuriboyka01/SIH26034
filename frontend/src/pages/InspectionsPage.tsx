import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ChevronLeft, ChevronRight, ClipboardList, Image as ImageIcon, Plus, Search } from 'lucide-react';
import { getInspections, type InspectionListItem } from '../api/inspections';
import { Alert, EmptyState, LoadingState, StatusBadge } from '../components/ui';

const statusFilters = [
  { value: '', label: 'All' },
  { value: 'PASS', label: 'Compliant' },
  { value: 'FAIL', label: 'Non-compliant' },
  { value: 'REVIEW', label: 'Needs review' },
  { value: 'NOT_ANALYSED', label: 'Not analysed' },
];

export default function InspectionsPage() {
  const [inspections, setInspections] = useState<InspectionListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  const [searchInput, setSearchInput] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [complianceStatus, setComplianceStatus] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Live search: debounce keystrokes into a single applied filter, no submit button needed.
  useEffect(() => {
    const handle = setTimeout(() => {
      setPage(1);
      setAppliedSearch(searchInput);
    }, 350);
    return () => clearTimeout(handle);
  }, [searchInput]);

  useEffect(() => {
    setLoading(true);
    setFailed(false);
    getInspections({ search: appliedSearch || undefined, compliance_status: complianceStatus || undefined, skip: (page - 1) * pageSize, limit: pageSize })
      .then((data) => { setInspections(data.items); setTotalCount(data.totalCount); })
      .catch(() => setFailed(true))
      .finally(() => setLoading(false));
  }, [appliedSearch, complianceStatus, page]);

  const pages = Math.max(1, Math.ceil(totalCount / pageSize));
  const isFiltered = Boolean(appliedSearch || complianceStatus);

  return (
    <div className="space-y-8 max-w-[1920px] mx-auto">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <p className="text-sm text-[var(--text-muted)]">
          {loading
            ? 'Loading register…'
            : `${totalCount} inspection${totalCount === 1 ? '' : 's'} recorded${isFiltered ? `, ${inspections.length} match your filters` : ''}`}
        </p>
        <Link to="/inspections/new" className="neo-button-primary whitespace-nowrap">
          <Plus size={18} /> New inspection
        </Link>
      </section>

      <section className="depth-1 rounded-xl p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
          <div className="relative flex-1 max-w-sm">
            <label className="sr-only" htmlFor="inspectionSearch">Search inspections</label>
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" />
            <input
              id="inspectionSearch"
              className="neo-input pl-12 bg-[var(--surface-pale)] border-[var(--line)]"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search inspection ID, product, or brand"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {statusFilters.map((filter) => (
              <button
                key={filter.value || 'all'}
                type="button"
                onClick={() => { setPage(1); setComplianceStatus(filter.value); }}
                className={`px-3.5 py-2 rounded-full text-xs font-semibold border transition-colors ${
                  complianceStatus === filter.value
                    ? 'bg-[var(--text)] text-[var(--canvas)] border-[var(--text)]'
                    : 'bg-[var(--surface)] text-[var(--text-muted)] border-[var(--line-strong)] hover:border-[var(--text-faint)]'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {failed && <Alert tone="error">The inspection register could not be loaded. Check the API connection and try again.</Alert>}

      {loading ? (
        <LoadingState label="Loading inspection register" />
      ) : inspections.length === 0 ? (
        <EmptyState
          icon={<ClipboardList size={32} />}
          title={isFiltered ? 'No cases match your filters' : 'No cases logged yet'}
          description={isFiltered ? 'Try a different search term or clear a filter.' : 'Open your first evidence record to begin compliance analysis.'}
          action={!isFiltered ? <Link to="/inspections/new" className="neo-button-primary mt-4">Create inspection</Link> : undefined}
        />
      ) : (
        <div className="space-y-6">
          {/* Desktop Table */}
          <section className="hidden md:block depth-2 overflow-hidden rounded-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[900px]">
                <thead className="bg-[var(--surface-raised)] border-b border-[var(--line-strong)]">
                  <tr>
                    <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] w-[120px]">ID</th>
                    <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] min-w-[200px]">Product / Brand</th>
                    <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] text-center w-[100px]">Evidence</th>
                    <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] w-[140px]">Lifecycle</th>
                    <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] w-[140px]">Compliance</th>
                    <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] text-right w-[120px]">Created</th>
                    <th className="px-6 py-4 w-14"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--line)]">
                  {inspections.map((inspection) => (
                    <tr key={inspection.id} className="group transition-colors hover:bg-[var(--surface-pale)]">
                      <td className="px-6 py-4 align-middle">
                        <Link to={`/inspections/${inspection.id}`} className="font-mono text-xs font-bold text-[var(--brand)] px-2 py-1 bg-[var(--brand-soft)] rounded hover:bg-[var(--brand)] hover:text-white transition-colors">
                          {inspection.inspection_number}
                        </Link>
                      </td>
                      <td className="px-6 py-4 align-middle">
                        <p className="text-sm font-bold text-[var(--text)] group-hover:text-[var(--brand)] transition-colors">{inspection.product_name}</p>
                        <p className="mt-1 text-xs font-medium text-[var(--text-muted)]">{inspection.brand}</p>
                      </td>
                      <td className="px-6 py-4 align-middle text-center">
                        <span className="inline-flex items-center justify-center gap-1.5 px-2 py-1 bg-[var(--surface)] border border-[var(--line-strong)] rounded-md font-mono text-xs font-semibold text-[var(--text-muted)] shadow-sm">
                          <ImageIcon size={14} className="text-[var(--text-faint)]" /> {inspection.image_count}
                        </span>
                      </td>
                      <td className="px-6 py-4 align-middle">
                        <StatusBadge value={inspection.status} />
                      </td>
                      <td className="px-6 py-4 align-middle">
                        <StatusBadge value={inspection.compliance_status} />
                      </td>
                      <td className="px-6 py-4 align-middle text-right">
                        <p className="font-mono text-xs font-medium text-[var(--text-muted)]">
                          {new Date(inspection.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
                        </p>
                      </td>
                      <td className="px-6 py-4 align-middle text-right">
                        <Link to={`/inspections/${inspection.id}`} className="inline-flex w-8 h-8 rounded-full bg-[var(--surface)] border border-[var(--line-strong)] items-center justify-center text-[var(--text-faint)] group-hover:bg-[var(--brand)] group-hover:border-[var(--brand)] group-hover:text-white shadow-sm transition-all" aria-label={`Open ${inspection.inspection_number}`}>
                          <ArrowRight size={14} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Mobile List */}
          <section className="space-y-4 md:hidden">
            {inspections.map((inspection) => (
              <Link key={inspection.id} to={`/inspections/${inspection.id}`} className="block bg-[var(--surface)] border border-[var(--line-strong)] rounded-xl p-5 shadow-sm active:bg-[var(--surface-pale)] transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-mono text-[10px] font-bold text-[var(--brand)] px-2 py-0.5 bg-[var(--brand-soft)] rounded inline-block mb-2">
                      {inspection.inspection_number}
                    </p>
                    <p className="truncate text-base font-bold text-[var(--text)]">{inspection.product_name}</p>
                    <p className="mt-1 text-xs font-medium text-[var(--text-muted)]">{inspection.brand}</p>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-[var(--surface-raised)] border border-[var(--line)] flex items-center justify-center shrink-0">
                    <ArrowRight size={14} className="text-[var(--text-muted)]" />
                  </div>
                </div>
                <div className="mt-5 pt-4 border-t border-[var(--line)] flex flex-wrap gap-2 items-center">
                  <StatusBadge value={inspection.status} />
                  <StatusBadge value={inspection.compliance_status} />
                  <span className="ml-auto inline-flex items-center gap-1 px-2 py-1 bg-[var(--surface-raised)] border border-[var(--line)] rounded text-[11px] font-mono font-medium text-[var(--text-muted)]">
                    <ImageIcon size={12} className="text-[var(--text-faint)]" /> {inspection.image_count}
                  </span>
                </div>
              </Link>
            ))}
          </section>
        </div>
      )}

      {pages > 1 && (
        <div className="flex items-center justify-between px-2 pt-2">
          <p className="font-mono text-xs font-bold uppercase tracking-wider text-[var(--text-faint)]">Page {page} of {pages}</p>
          <div className="flex gap-2">
            <button className="w-10 h-10 rounded-full bg-[var(--surface)] border border-[var(--line-strong)] flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--brand)] hover:border-[var(--brand)] disabled:opacity-50 disabled:pointer-events-none shadow-sm transition-colors" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1} aria-label="Previous page">
              <ChevronLeft size={18} />
            </button>
            <button className="w-10 h-10 rounded-full bg-[var(--surface)] border border-[var(--line-strong)] flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--brand)] hover:border-[var(--brand)] disabled:opacity-50 disabled:pointer-events-none shadow-sm transition-colors" onClick={() => setPage((current) => Math.min(pages, current + 1))} disabled={page === pages} aria-label="Next page">
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
