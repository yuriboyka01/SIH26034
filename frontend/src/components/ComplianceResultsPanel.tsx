import { AlertTriangle, CheckCircle2, FileSearch, Scale, Info, ChevronDown, ChevronRight, Check } from 'lucide-react';
import { useState } from 'react';
import type { ComplianceReport, RuleResult } from '../api/compliance';
import { EvidenceViewer } from './EvidenceViewer';
import { EmptyState, SectionHeader, StatusBadge } from './ui';

export function ComplianceResultsPanel({ reports, isAnalyzing, images = [] }: { reports: ComplianceReport[]; isAnalyzing: boolean; images?: { id: string; url: string }[] }) {
  if (isAnalyzing) {
    return (
      <section className="depth-2 overflow-hidden flex flex-col">
        <SectionHeader eyebrow="05" title="Compliance Findings" description="Awaiting rule checks against the legal framework." />
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[var(--canvas)] m-4 rounded-xl border border-dashed border-[var(--line-strong)]">
          <div className="w-14 h-14 bg-[var(--surface)] rounded-full shadow-sm border border-[var(--line)] flex items-center justify-center mb-4">
            <Scale size={24} className="text-[var(--text-faint)]" />
          </div>
          <p className="text-base font-bold text-[var(--text)]">Evaluating rules</p>
          <p className="mt-2 max-w-xs text-sm leading-relaxed text-[var(--text-muted)]">Comparing extracted declarations against Legal Metrology frameworks...</p>
        </div>
      </section>
    );
  }

  if (!reports.length) {
    return (
      <section className="depth-2 overflow-hidden flex flex-col">
        <SectionHeader eyebrow="05" title="Compliance Findings" description="Awaiting evidence to assess compliance." />
        <div className="flex-1">
          <EmptyState icon={<Scale size={32} />} title="Rule evaluation pending" description="Upload package evidence and run analysis to create an evidence-linked compliance assessment." />
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-6 flex flex-col">
      {reports.map((report) => { 
        const imageUrl = images.find((image) => image.id === report.image_id)?.url;
        const breakdowns = report.category_breakdown || [];
        
        // Ensure we prioritize categories with FAIL or REVIEW
        const sortedBreakdowns = [...breakdowns].sort((a, b) => {
          if (a.failed_count !== b.failed_count) return b.failed_count - a.failed_count;
          if (a.review_count !== b.review_count) return b.review_count - a.review_count;
          return 0;
        });

        return (
          <section key={report.image_id} className="depth-2 overflow-hidden flex flex-col">
            <SectionHeader 
              eyebrow="05" 
              title="Grouped Compliance Findings" 
              description={`${report.total_rules_checked} rules evaluated against extracted declarations.`} 
            />
            
            <div className="flex-1 bg-[var(--canvas)] p-4 space-y-6">
              {sortedBreakdowns.map((cat) => (
                <CategoryGroup key={cat.category} category={cat} results={report.rule_results.filter(r => r.category === cat.category)} imageUrl={imageUrl} />
              ))}
            </div>
          </section>
        ); 
      })}
    </div>
  );
}

function CategoryGroup({ category, results, imageUrl }: { category: any; results: RuleResult[]; imageUrl?: string }) {
  const [expanded, setExpanded] = useState(category.failed_count > 0 || category.review_count > 0);
  
  // Sort results within category: FAIL -> REVIEW -> PASS -> NOT_APPLICABLE
  const sortedResults = [...results].sort((a, b) => {
    const rank: Record<string, number> = { FAIL: 1, REVIEW: 2, PASS: 3, NOT_APPLICABLE: 4 };
    return (rank[a.status] || 99) - (rank[b.status] || 99);
  });

  return (
    <div className="border border-[var(--line)] rounded-xl overflow-hidden bg-[var(--surface)] shadow-sm">
      <div 
        className="flex flex-wrap items-center justify-between p-4 cursor-pointer hover:bg-[var(--surface-raised)] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          {expanded ? <ChevronDown size={18} className="text-[var(--text-faint)]" /> : <ChevronRight size={18} className="text-[var(--text-faint)]" />}
          <div>
            <h3 className="text-base font-bold text-[var(--text)]">{category.label}</h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">{category.total} rules checked</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {category.failed_count > 0 && <StatusBadge value="FAIL" />}
          {category.failed_count === 0 && category.review_count > 0 && <StatusBadge value="REVIEW" />}
          {category.failed_count === 0 && category.review_count === 0 && category.passed_count > 0 && <StatusBadge value="PASS" />}
          <div className="flex gap-2 text-xs font-semibold ml-2">
            {category.passed_count > 0 && <span className="text-[var(--success)]">{category.passed_count} Pass</span>}
            {category.failed_count > 0 && <span className="text-[var(--danger)]">{category.failed_count} Fail</span>}
            {category.review_count > 0 && <span className="text-[var(--warning)]">{category.review_count} Review</span>}
            {category.not_applicable_count > 0 && <span className="text-[var(--text-faint)]">{category.not_applicable_count} N/A</span>}
          </div>
        </div>
      </div>
      
      {expanded && (
        <div className="border-t border-[var(--line)] p-4 bg-[var(--canvas)] space-y-4">
          {sortedResults.map(result => (
            <RuleFinding key={result.rule_id} result={result} imageUrl={imageUrl} />
          ))}
        </div>
      )}
    </div>
  );
}

function RuleFinding({ result, imageUrl }: { result: RuleResult; imageUrl?: string }) {
  const [detailsOpen, setDetailsOpen] = useState(result.status === 'FAIL' || result.status === 'REVIEW');
  
  const isFailure = result.status === 'FAIL'; 
  const isPass = result.status === 'PASS';
  const Icon = isFailure ? AlertTriangle : isPass ? CheckCircle2 : Info;
  
  const colors = {
    FAIL: {
      bg: 'bg-[var(--danger-soft)]/30 border-[var(--danger-soft)]',
      iconBg: 'bg-[var(--danger)] text-white',
      bar: 'bg-[var(--danger)]',
      title: 'text-[var(--danger-strong)]'
    },
    PASS: {
      bg: 'bg-[var(--surface)] border-[var(--success-soft)]',
      iconBg: 'bg-[var(--success-soft)] text-[var(--success)]',
      bar: 'bg-[var(--success)]',
      title: 'text-[var(--text)]'
    },
    REVIEW: {
      bg: 'bg-[var(--warning-soft)]/30 border-[var(--warning-soft)]',
      iconBg: 'bg-[var(--warning)] text-white',
      bar: 'bg-[var(--warning)]',
      title: 'text-[var(--warning-strong)]'
    },
    NOT_APPLICABLE: {
      bg: 'bg-[var(--surface-raised)] border-[var(--line)] opacity-80',
      iconBg: 'bg-[var(--line)] text-[var(--text-muted)]',
      bar: 'bg-[var(--line-strong)]',
      title: 'text-[var(--text-muted)]'
    }
  };

  const theme = colors[result.status as keyof typeof colors] || colors.REVIEW;
  const confPercent = result.confidence != null ? Math.round(result.confidence * 100) : null;

  return (
    <article className={`rounded-xl border ${theme.bg} overflow-hidden relative`}>
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${theme.bar}`}></div>
      
      {/* Compact Header */}
      <div 
        className="p-3 pl-4 flex flex-wrap items-center justify-between cursor-pointer hover:bg-black/5 transition-colors gap-3"
        onClick={() => setDetailsOpen(!detailsOpen)}
      >
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${theme.iconBg}`}>
            <Icon size={14} />
          </div>
          <div className="truncate">
            <h4 className={`text-sm font-bold truncate ${theme.title}`}>{result.rule_name}</h4>
            <div className="flex items-center gap-2 mt-0.5 text-[10px] text-[var(--text-muted)] font-mono">
              <span>{result.rule_id}</span>
              {confPercent !== null && result.status !== 'NOT_APPLICABLE' && (
                <>
                  <span className="text-[var(--line-strong)]">•</span>
                  <span>Conf {confPercent}%</span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <StatusBadge value={result.status} />
          {detailsOpen ? <ChevronDown size={16} className="text-[var(--text-faint)]" /> : <ChevronRight size={16} className="text-[var(--text-faint)]" />}
        </div>
      </div>
      
      {/* Expandable Details */}
      {detailsOpen && (
        <div className="p-4 pl-5 border-t border-[var(--line)] space-y-4 text-sm">
          
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="bg-[var(--surface)] border border-[var(--line)] p-3 rounded-lg shadow-sm">
              <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] mb-1">Requirement</p>
              <p className="font-medium text-[var(--text)]">{result.expected}</p>
            </div>
            {result.status !== 'NOT_APPLICABLE' && (
              <div className="bg-[var(--surface)] border border-[var(--line)] p-3 rounded-lg shadow-sm">
                <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] mb-1">Detected Value</p>
                <p className="font-mono text-[var(--text)] font-semibold break-words">{result.actual || 'Not detected'}</p>
              </div>
            )}
          </div>
          
          <p className="text-[var(--text)] leading-relaxed bg-[var(--surface-raised)] p-3 rounded-lg border border-[var(--line)]">
            <span className="font-semibold block mb-1 text-[11px] uppercase tracking-wider text-[var(--text-muted)]">Explanation</span>
            {result.message}
          </p>

          {result.remediation && (
            <div className={`p-3 rounded-lg border ${isFailure ? 'bg-[var(--danger-soft)]/20 border-[var(--danger-soft)]' : 'bg-[var(--warning-soft)]/20 border-[var(--warning-soft)]'}`}>
              <p className={`font-semibold mb-1 flex items-center gap-1.5 text-[11px] uppercase tracking-wider ${isFailure ? 'text-[var(--danger)]' : 'text-[var(--warning)]'}`}>
                 Recommendation
              </p>
              <p className="text-[var(--text)]">{result.remediation}</p>
            </div>
          )}

          {result.evidence && (
            <div className="mt-2">
              <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] mb-2">Evidence Snippet</p>
              <EvidenceViewer evidence={result.evidence} imageUrl={imageUrl} status={result.status} />
            </div>
          )}

          <div className="flex items-center gap-1.5 pt-2 mt-2 border-t border-[var(--line)]">
            <FileSearch size={14} className="text-[var(--text-faint)]" />
            <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">Source: {result.source_reference}</p>
          </div>
        </div>
      )}
    </article>
  );
}
