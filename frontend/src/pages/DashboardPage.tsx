/**
 * Dashboard page — Phase 5 Enforcement Dashboard with Compliance KPIs.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardAnalytics, type DashboardAnalyticsResponse } from '../api/dashboard';
import ViolationChart from '../components/ViolationChart';
import {
  ClipboardList,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  PlusCircle,
  ArrowRight,
  Loader2,
  BarChart3
} from 'lucide-react';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const analytics = await getDashboardAnalytics();
        setData(analytics);
      } catch (err) {
        console.error('Failed to fetch dashboard analytics:', err);
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

  const kpis = data?.kpis;

  const statCards = [
    {
      label: 'Compliant',
      value: kpis?.compliant_count || 0,
      icon: CheckCircle2,
      color: 'from-emerald-500 to-emerald-600',
      bgColor: 'bg-emerald-500/10',
      textColor: 'text-emerald-400',
    },
    {
      label: 'Non-Compliant',
      value: kpis?.non_compliant_count || 0,
      icon: XCircle,
      color: 'from-red-500 to-red-600',
      bgColor: 'bg-red-500/10',
      textColor: 'text-red-400',
    },
    {
      label: 'Needs Review',
      value: kpis?.review_count || 0,
      icon: AlertTriangle,
      color: 'from-amber-500 to-amber-600',
      bgColor: 'bg-amber-500/10',
      textColor: 'text-amber-400',
    },
    {
      label: 'Not Analysed',
      value: kpis?.not_analysed_count || 0,
      icon: ClipboardList,
      color: 'from-slate-500 to-slate-600',
      bgColor: 'bg-slate-500/10',
      textColor: 'text-slate-400',
    },
  ];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Enforcement Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Total Inspections: <span className="font-semibold text-white">{kpis?.total_inspections || 0}</span>
            {' '}· Compliance Rate: <span className="font-semibold text-white">{kpis?.compliance_rate || 0}%</span>
          </p>
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Top Violations */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl flex flex-col">
          <div className="flex items-center gap-2 p-5 border-b border-slate-700/50">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-semibold text-white">Top Violations</h2>
          </div>
          <div className="p-5 flex-1">
            <ViolationChart violations={data?.top_violations || []} />
          </div>
        </div>

        {/* Recent Inspections */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl flex flex-col">
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

          {!data?.recent_inspections || data.recent_inspections.length === 0 ? (
            <div className="p-8 text-center flex-1 flex flex-col items-center justify-center">
              <ClipboardList className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No inspections yet</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-700/50 flex-1">
              {data.recent_inspections.map((inspection) => (
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
                    <ComplianceBadge status={inspection.compliance_status} />
                    <ArrowRight className="w-4 h-4 text-slate-500" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
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
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
        styles[status] || styles['NOT_ANALYSED']
      }`}
    >
      {labels[status] || status}
    </span>
  );
}
