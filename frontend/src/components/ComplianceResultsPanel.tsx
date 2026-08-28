import React from 'react';
import { ComplianceReport, RuleResult } from '../api/compliance';
import { EvidenceViewer } from './EvidenceViewer';

interface ComplianceResultsPanelProps {
  reports: ComplianceReport[];
  isAnalyzing: boolean;
}

const statusColors = {
  PASS: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  FAIL: 'bg-red-100 text-red-800 border-red-200',
  REVIEW: 'bg-amber-100 text-amber-800 border-amber-200',
  NOT_APPLICABLE: 'bg-slate-100 text-slate-800 border-slate-200',
};

const bgColors = {
  PASS: 'bg-emerald-50 border-emerald-100',
  FAIL: 'bg-red-50 border-red-100',
  REVIEW: 'bg-amber-50 border-amber-100',
  NOT_APPLICABLE: 'bg-slate-50 border-slate-100',
};

export const ComplianceResultsPanel: React.FC<ComplianceResultsPanelProps> = ({ reports, isAnalyzing }) => {
  if (isAnalyzing) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Running Compliance Checks...
        </h3>
        <p className="text-sm text-slate-500">Checking declarations against Legal Metrology Rules, 2011.</p>
      </div>
    );
  }

  if (!reports || reports.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">Compliance Rules Engine</h3>
        <p className="text-sm text-slate-500">
          Run analysis to check the extracted product info against the Legal Metrology Rules, 2011.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {reports.map((report) => (
        <div key={report.image_id} className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
          {/* Header */}
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-slate-800">Compliance Report</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${statusColors[report.overall_status]}`}>
              {report.overall_status}
            </span>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-5 divide-x divide-slate-100 border-b border-slate-100 text-center text-sm bg-white">
            <div className="p-3">
              <div className="text-slate-500">Total Checked</div>
              <div className="font-semibold text-slate-800 text-lg">{report.total_rules_checked}</div>
            </div>
            <div className="p-3 bg-emerald-50">
              <div className="text-emerald-700">Passed</div>
              <div className="font-semibold text-emerald-800 text-lg">{report.passed_count}</div>
            </div>
            <div className="p-3 bg-red-50">
              <div className="text-red-700">Failed</div>
              <div className="font-semibold text-red-800 text-lg">{report.failed_count}</div>
            </div>
            <div className="p-3 bg-amber-50">
              <div className="text-amber-700">Review</div>
              <div className="font-semibold text-amber-800 text-lg">{report.review_count}</div>
            </div>
            <div className="p-3 bg-slate-50">
              <div className="text-slate-600">N/A</div>
              <div className="font-semibold text-slate-700 text-lg">{report.not_applicable_count}</div>
            </div>
          </div>

          {/* Rule Results List */}
          <div className="divide-y divide-slate-100">
            {report.rule_results.map((rr: RuleResult) => (
              <div key={rr.rule_id} className={`p-4 border-l-4 ${bgColors[rr.status]} hover:opacity-90 transition-opacity`}>
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-white">
                      {rr.rule_id}
                    </span>
                    <h4 className="font-semibold text-slate-800">{rr.rule_name}</h4>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-1 rounded border ${statusColors[rr.status]}`}>
                    {rr.status}
                  </span>
                </div>
                
                <p className="text-sm text-slate-700 mb-3">{rr.message}</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs bg-white/50 rounded p-3 border border-slate-200/50">
                  <div className="space-y-4">
                    <div>
                      <span className="font-semibold text-slate-500 block mb-1">Requirement:</span>
                      <span className="text-slate-700 block">{rr.expected}</span>
                      <span className="text-slate-400 block mt-1 italic text-[10px]">{rr.source_reference}</span>
                    </div>
                    {rr.field && (
                      <div>
                        <span className="font-semibold text-slate-500 block mb-1">Observation ({rr.field}):</span>
                        {rr.actual ? (
                          <span className="font-mono bg-white px-2 py-1 border border-slate-200 rounded text-slate-800">
                            {rr.actual}
                          </span>
                        ) : (
                          <span className="italic text-slate-400">Not detected</span>
                        )}
                      </div>
                    )}
                  </div>
                  {rr.evidence && (
                    <div>
                      <EvidenceViewer evidence={rr.evidence} />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
