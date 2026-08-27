/**
 * Dashboard page — overview cards with inspection statistics.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardStats, getInspections, type DashboardStats, type InspectionListItem } from '../api/inspections';
import {
  ClipboardList,
  FileCheck,
  ImageIcon,
  AlertTriangle,
  PlusCircle,
  ArrowRight,
  Loader2,
} from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentInspections, setRecentInspections] = useState<InspectionListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, inspectionsData] = await Promise.all([
          getDashboardStats(),
          getInspections(),
        ]);
        setStats(statsData);
        setRecentInspections(inspectionsData.slice(0, 5));
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
      </div>
    );
  }

  const statCards = [
    {
      label: 'Total Inspections',
      value: stats?.total || 0,
      icon: ClipboardList,
      color: 'from-indigo-500 to-indigo-600',
      bgColor: 'bg-indigo-500/10',
      textColor: 'text-indigo-400',
    },
    {
      label: 'Created',
      value: stats?.created || 0,
      icon: FileCheck,
      color: 'from-cyan-500 to-cyan-600',
      bgColor: 'bg-cyan-500/10',
      textColor: 'text-cyan-400',
    },
    {
      label: 'Images Uploaded',
      value: stats?.images_uploaded || 0,
      icon: ImageIcon,
      color: 'from-amber-500 to-amber-600',
      bgColor: 'bg-amber-500/10',
      textColor: 'text-amber-400',
    },
    {
      label: 'Needs Review',
      value: stats?.needs_review || 0,
      icon: AlertTriangle,
      color: 'from-red-500 to-red-600',
      bgColor: 'bg-red-500/10',
      textColor: 'text-red-400',
    },
  ];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">Legal Metrology Compliance Overview</p>
        </div>
        <Link
          to="/inspections/new"
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white text-sm font-medium rounded-lg transition-all duration-200 shadow-lg shadow-indigo-500/25"
        >
          <PlusCircle className="w-4 h-4" />
          New Inspection
        </Link>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card, i) => (
          <div
            key={card.label}
            className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 hover:border-slate-600/50 transition-all duration-300"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`p-2 rounded-lg ${card.bgColor}`}>
                <card.icon className={`w-5 h-5 ${card.textColor}`} />
              </div>
            </div>
            <p className="text-2xl font-bold text-white">{card.value}</p>
            <p className="text-sm text-slate-400 mt-1">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Recent Inspections */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl">
        <div className="flex items-center justify-between p-5 border-b border-slate-700/50">
          <h2 className="text-lg font-semibold text-white">Recent Inspections</h2>
          <Link
            to="/inspections"
            className="flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            View All
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentInspections.length === 0 ? (
          <div className="p-8 text-center">
            <ClipboardList className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">No inspections yet</p>
            <Link
              to="/inspections/new"
              className="inline-flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300 mt-2 transition-colors"
            >
              Create your first inspection
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/50">
            {recentInspections.map((inspection) => (
              <Link
                key={inspection.id}
                to={`/inspections/${inspection.id}`}
                className="flex items-center justify-between p-4 hover:bg-slate-700/20 transition-colors"
              >
                <div>
                  <p className="text-sm font-medium text-white">{inspection.product_name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {inspection.inspection_number} · {inspection.brand}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={inspection.status} />
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
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
