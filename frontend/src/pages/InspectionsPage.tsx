/**
 * Inspections list page — server-side search, filter, and pagination.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getInspections, type InspectionListItem } from '../api/inspections';
import {
  ClipboardList,
  PlusCircle,
  ArrowRight,
  ImageIcon,
  Loader2,
  Search,
  ChevronLeft,
  ChevronRight,
  Filter
} from 'lucide-react';

export default function InspectionsPage() {
  const [inspections, setInspections] = useState<InspectionListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters & Pagination
  const [searchInput, setSearchInput] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [complianceStatus, setComplianceStatus] = useState<string>('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    const fetchInspections = async () => {
      setLoading(true);
      try {
        const data = await getInspections({
          search: appliedSearch || undefined,
          compliance_status: complianceStatus || undefined,
          skip: (page - 1) * pageSize,
          limit: pageSize,
        });
        setInspections(data.items);
        setTotalCount(data.totalCount);
      } catch (err) {
        console.error('Failed to fetch inspections:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchInspections();
  }, [appliedSearch, complianceStatus, page, pageSize]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setAppliedSearch(searchInput);
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPage(1);
    setComplianceStatus(e.target.value);
  };

  const totalPages = Math.ceil(totalCount / pageSize) || 1;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Inspections</h1>
          <p className="text-sm text-slate-400 mt-1">{totalCount} total inspections found</p>
        </div>
        <Link
          to="/inspections/new"
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white text-sm font-medium rounded-lg transition-all duration-200 shadow-lg shadow-indigo-500/25"
        >
          <PlusCircle className="w-4 h-4" />
          New Inspection
        </Link>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <form onSubmit={handleSearch} className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by product, brand, or number... (Press Enter)"
            className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
        </form>
        
        <div className="relative min-w-[200px]">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <select
            value={complianceStatus}
            onChange={handleStatusChange}
            className="w-full pl-10 pr-10 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer"
          >
            <option value="">All Compliance Statuses</option>
            <option value="PASS">Pass</option>
            <option value="FAIL">Fail</option>
            <option value="REVIEW">Needs Review</option>
            <option value="NOT_ANALYSED">Not Analysed</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64 bg-slate-800/50 border border-slate-700/50 rounded-xl">
          <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
        </div>
      ) : inspections.length === 0 ? (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-12 text-center">
          <ClipboardList className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 mb-2">
            {appliedSearch || complianceStatus ? 'No matching inspections found' : 'No inspections yet'}
          </p>
          {!appliedSearch && !complianceStatus && (
            <Link
              to="/inspections/new"
              className="inline-flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Create your first inspection
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>
      ) : (
        <>
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden mb-4">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Inspection
                    </th>
                    <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Product / Brand
                    </th>
                    <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Images
                    </th>
                    <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Lifecycle Status
                    </th>
                    <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Compliance
                    </th>
                    <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="w-10" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                  {inspections.map((inspection) => (
                    <tr
                      key={inspection.id}
                      className="hover:bg-slate-700/20 transition-colors"
                    >
                      <td className="px-5 py-4">
                        <Link
                          to={`/inspections/${inspection.id}`}
                          className="text-sm font-mono text-indigo-400 hover:text-indigo-300"
                        >
                          {inspection.inspection_number}
                        </Link>
                      </td>
                      <td className="px-5 py-4">
                        <p className="text-sm text-white">{inspection.product_name}</p>
                        <p className="text-xs text-slate-400">{inspection.brand}</p>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1.5 text-sm text-slate-300">
                          <ImageIcon className="w-3.5 h-3.5 text-slate-400" />
                          {inspection.image_count}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <LifecycleBadge status={inspection.status} />
                      </td>
                      <td className="px-5 py-4">
                        <ComplianceBadge status={inspection.compliance_status || 'NOT_ANALYSED'} />
                      </td>
                      <td className="px-5 py-4 text-sm text-slate-400 whitespace-nowrap">
                        {new Date(inspection.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-3 py-4">
                        <Link to={`/inspections/${inspection.id}`}>
                          <ArrowRight className="w-4 h-4 text-slate-500 hover:text-white transition-colors" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3">
              <span className="text-sm text-slate-400">
                Showing <span className="font-medium text-white">{(page - 1) * pageSize + 1}</span> to{' '}
                <span className="font-medium text-white">
                  {Math.min(page * pageSize, totalCount)}
                </span>{' '}
                of <span className="font-medium text-white">{totalCount}</span> results
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-slate-300 font-medium px-2">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function LifecycleBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    CREATED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    IMAGES_UPLOADED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    PROCESSING: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    COMPLETED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    NEEDS_REVIEW: 'bg-red-500/10 text-red-400 border-red-500/20',
  };

  const labels: Record<string, string> = {
    CREATED: 'Created',
    IMAGES_UPLOADED: 'Images Uploaded',
    PROCESSING: 'Processing',
    COMPLETED: 'Completed',
    NEEDS_REVIEW: 'Needs Review',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] sm:text-xs font-medium border ${
        styles[status] || styles['CREATED']
      }`}
    >
      {labels[status] || status}
    </span>
  );
}

function ComplianceBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    PASS: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    FAIL: 'bg-red-500/10 text-red-400 border-red-500/20',
    REVIEW: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    NOT_ANALYSED: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  };

  const labels: Record<string, string> = {
    PASS: 'Pass',
    FAIL: 'Fail',
    REVIEW: 'Review',
    NOT_ANALYSED: 'Not Analysed',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] sm:text-xs font-medium border ${
        styles[status] || styles['NOT_ANALYSED']
      }`}
    >
      {labels[status] || status}
    </span>
  );
}
