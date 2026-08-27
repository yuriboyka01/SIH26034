/**
 * Inspections list page — table of all user inspections.
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
} from 'lucide-react';

export default function InspectionsPage() {
  const [inspections, setInspections] = useState<InspectionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchInspections = async () => {
      try {
        const data = await getInspections();
        setInspections(data);
      } catch (err) {
        console.error('Failed to fetch inspections:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchInspections();
  }, []);

  const filtered = inspections.filter(
    (i) =>
      i.product_name.toLowerCase().includes(search.toLowerCase()) ||
      i.brand.toLowerCase().includes(search.toLowerCase()) ||
      i.inspection_number.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Inspections</h1>
          <p className="text-sm text-slate-400 mt-1">{inspections.length} total inspections</p>
        </div>
        <Link
          to="/inspections/new"
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white text-sm font-medium rounded-lg transition-all duration-200 shadow-lg shadow-indigo-500/25"
        >
          <PlusCircle className="w-4 h-4" />
          New Inspection
        </Link>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by product, brand, or number..."
          className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
        />
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-12 text-center">
          <ClipboardList className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 mb-2">
            {search ? 'No matching inspections found' : 'No inspections yet'}
          </p>
          {!search && (
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
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
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
                  Status
                </th>
                <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Date
                </th>
                <th className="w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/30">
              {filtered.map((inspection) => (
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
                    <StatusBadge status={inspection.status} />
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-400">
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
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
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
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
        styles[status] || styles['CREATED']
      }`}
    >
      {labels[status] || status}
    </span>
  );
}
