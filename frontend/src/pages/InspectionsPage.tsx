import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Image as ImageIcon,
  Plus,
  Search,
  X,
} from 'lucide-react';
import { getInspections, type InspectionListItem } from '../api/inspections';
import { Alert, EmptyState, LoadingState, StatusBadge } from '../components/ui';

const complianceFilters = [
  { value: '', label: 'All outcomes' },
  { value: 'PASS', label: 'Compliant' },
  { value: 'FAIL', label: 'Non-compliant' },
  { value: 'REVIEW', label: 'Needs review' },
  { value: 'NOT_ANALYSED', label: 'Not analysed' },
];

export default function InspectionsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlSearch = searchParams.get('search') || '';

  const [inspections, setInspections] = useState<InspectionListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  const [searchInput, setSearchInput] = useState(urlSearch);
  const [appliedSearch, setAppliedSearch] = useState(urlSearch);
  const [complianceStatus, setComplianceStatus] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    const q = searchParams.get('search') || '';
    setSearchInput(q);
    setAppliedSearch(q);
    setPage(1);
  }, [searchParams]);


  // Debounced live search
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
    getInspections({
      search: appliedSearch || undefined,
      compliance_status: complianceStatus || undefined,
      skip: (page - 1) * pageSize,
      limit: pageSize,
    })
      .then((data) => {
        setInspections(data.items);
        setTotalCount(data.totalCount);
      })
      .catch(() => {
        setFailed(true);
        setInspections([]);
        setTotalCount(0);
      })
      .finally(() => setLoading(false));
  }, [appliedSearch, complianceStatus, page]);

  const pages = Math.max(1, Math.ceil(totalCount / pageSize));
  const isFiltered = Boolean(appliedSearch || complianceStatus);

  const clearFilters = () => {
    setSearchInput('');
    setAppliedSearch('');
    setComplianceStatus('');
    setSearchParams({});
    setPage(1);
  };

  return (
    <div className="space-y-6 sm:space-y-8 max-w-[1920px] mx-auto">
      {/* Header section */}
      <section className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="heading-page">Inspection register</h2>
          <p className="text-body mt-1 text-xs sm:text-sm">
            {loading
              ? 'Loading register…'
              : `${totalCount} inspection${totalCount === 1 ? '' : 's'} recorded${isFiltered ? `, ${inspections.length} matching filter` : ''}`}
          </p>
        </div>
        <Link to="/inspections/new" className="neo-button-primary whitespace-nowrap w-full sm:w-auto justify-center shadow-sm">
          <Plus size={18} /> New inspection
        </Link>
      </section>

      {failed && <Alert tone="error">The inspection register could not be loaded. Check the API connection and try again.</Alert>}

      {/* Filter and search controls */}
      <section className="depth-1 p-3.5 sm:p-4 rounded-xl border border-[var(--line)]">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1 min-w-0">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" />
            <input
              className="neo-input pl-10 pr-9 !min-h-[42px] h-10 text-xs sm:text-sm"
              placeholder="Search product, brand, or record ID"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            {searchInput && (
              <button
                type="button"
                onClick={() => setSearchInput('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-faint)] hover:text-[var(--text)]"
                aria-label="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <select
              className="neo-select !min-h-[42px] h-10 text-xs sm:text-sm flex-1 sm:w-auto sm:min-w-[160px]"
              value={complianceStatus}
              onChange={(e) => {
                setComplianceStatus(e.target.value);
                setPage(1);
              }}
              aria-label="Filter by compliance outcome"
            >
              {complianceFilters.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>

            {isFiltered && (
              <button
                className="neo-button-secondary !min-h-[42px] h-10 !px-3 text-xs font-semibold whitespace-nowrap"
                onClick={clearFilters}
              >
                <X size={14} /> Clear
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Main listings */}
      {loading ? (
        <LoadingState label="Loading inspection register" />
      ) : inspections.length === 0 ? (
        <EmptyState
          icon={<ClipboardList size={32} />}
          title={isFiltered ? 'No cases match your filters' : 'No cases logged yet'}
          description={isFiltered ? 'Try a different search term or clear a filter.' : 'Open your first evidence record to begin compliance analysis.'}
          action={!isFiltered ? <Link to="/inspections/new" className="neo-button-primary mt-4 w-full sm:w-auto">Create inspection</Link> : undefined}
        />
      ) : (
        <div className="space-y-4 sm:space-y-6">
          {/* Desktop Table */}
          <section className="hidden md:block depth-2 overflow-hidden rounded-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[850px]">
                <thead className="bg-[var(--surface-raised)] border-b border-[var(--line-strong)]">
                  <tr>
                    <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] w-[160px]">ID</th>
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
                        <Link to={`/inspections/${inspection.id}`} className="font-mono text-xs font-bold text-[var(--brand)] px-2 py-1 bg-[var(--brand-soft)] rounded hover:bg-[var(--brand)] hover:text-white transition-colors whitespace-nowrap inline-block">
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

          {/* Mobile List Cards */}
          <section className="space-y-3 md:hidden">
            {inspections.map((inspection) => (
              <Link 
                key={inspection.id} 
                to={`/inspections/${inspection.id}`} 
                className="block bg-[var(--surface)] border border-[var(--line-strong)] rounded-xl p-4 shadow-sm active:bg-[var(--surface-pale)] transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <span className="font-mono text-[10px] font-bold text-[var(--brand)] px-2 py-0.5 bg-[var(--brand-soft)] rounded inline-block mb-1.5">
                      {inspection.inspection_number}
                    </span>
                    <p className="truncate text-base font-bold text-[var(--text)]">{inspection.product_name}</p>
                    <p className="mt-0.5 text-xs font-medium text-[var(--text-muted)]">{inspection.brand}</p>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-[var(--surface-raised)] border border-[var(--line)] flex items-center justify-center shrink-0 text-[var(--text-muted)]">
                    <ArrowRight size={14} />
                  </div>
                </div>
                
                <div className="mt-3 pt-3 border-t border-[var(--line)] flex flex-wrap gap-2 items-center justify-between">
                  <div className="flex flex-wrap gap-1.5 items-center">
                    <StatusBadge value={inspection.status} />
                    <StatusBadge value={inspection.compliance_status} />
                  </div>
                  <div className="flex items-center gap-2 text-[11px] font-mono font-medium text-[var(--text-faint)]">
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-[var(--surface-raised)] rounded border border-[var(--line)]">
                      <ImageIcon size={11} /> {inspection.image_count}
                    </span>
                    <span>{new Date(inspection.created_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}</span>
                  </div>
                </div>
              </Link>
            ))}
          </section>
        </div>
      )}

      {/* Pagination */}
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
