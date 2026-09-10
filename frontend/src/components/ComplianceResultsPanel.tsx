import { AlertTriangle, CheckCircle2, FileSearch, Scale, Info } from 'lucide-react';
import type { ComplianceReport, RuleResult } from '../api/compliance';
import { EvidenceViewer } from './EvidenceViewer';
import { EmptyState, SectionHeader, StatusBadge } from './ui';

export function ComplianceResultsPanel({ reports, isAnalyzing, images = [] }: { reports: ComplianceReport[]; isAnalyzing: boolean; images?: { id: string; url: string }[] }) {
  if (isAnalyzing) {
    return (
      <section className="depth-2 overflow-hidden h-full flex flex-col">
        <SectionHeader eyebrow="03 / Rule Evaluation" title="Compliance Findings" description="Awaiting rule checks against the legal framework." />
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
      <section className="depth-2 overflow-hidden h-full flex flex-col">
        <SectionHeader eyebrow="03 / Rule Evaluation" title="Compliance Findings" description="Awaiting evidence to assess compliance." />
        <div className="flex-1">
          <EmptyState icon={<Scale size={32} />} title="Rule evaluation pending" description="Upload package evidence and run analysis to create an evidence-linked compliance assessment." />
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      {reports.map((report) => { 
        const imageUrl = images.find((image) => image.id === report.image_id)?.url; 
        return (
          <section key={report.image_id} className="depth-2 overflow-hidden flex flex-col flex-1">
            <SectionHeader 
              eyebrow={`03 / Rule Evaluation`} 
              title="Compliance Findings" 
              description={`${report.total_rules_checked} rules evaluated against extracted declarations.`} 
              action={<StatusBadge value={report.overall_status} />} 
            />
            
            <div className="grid grid-cols-4 bg-[var(--surface-raised)] border-b border-[var(--line)]">
              {[
                { label: 'Passed', value: report.passed_count, tone: 'text-[var(--success)]', border: 'border-[var(--success-soft)]' }, 
                { label: 'Failed', value: report.failed_count, tone: 'text-[var(--danger)]', border: 'border-[var(--danger-soft)]' }, 
                { label: 'Review', value: report.review_count, tone: 'text-[var(--warning)]', border: 'border-[var(--warning-soft)]' }, 
                { label: 'N/A', value: report.not_applicable_count, tone: 'text-[var(--text-muted)]', border: 'border-[var(--line)]' }
              ].map((metric) => (
                <div key={metric.label} className={`border-r border-[var(--line)] px-4 py-4 last:border-r-0 relative overflow-hidden bg-[var(--surface)]`}>
                  <div className={`absolute bottom-0 left-0 w-full h-0.5 ${metric.border}`}></div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">{metric.label}</p>
                  <p className={`mt-1 font-mono text-2xl font-bold ${metric.tone}`}>{metric.value}</p>
                </div>
              ))}
            </div>
            
            <div className="flex-1 overflow-y-auto bg-[var(--canvas)] p-4 space-y-4">
              {report.rule_results.map((result) => <RuleFinding key={result.rule_id} result={result} imageUrl={imageUrl} />)}
            </div>
          </section>
        ); 
      })}
    </div>
  );
}

function RuleFinding({ result, imageUrl }: { result: RuleResult; imageUrl?: string }) {
  const isFailure = result.status === 'FAIL'; 
  const isPass = result.status === 'PASS';
  const Icon = isFailure ? AlertTriangle : isPass ? CheckCircle2 : Info;
  
  const colors = {
    FAIL: {
      bg: 'bg-[var(--surface)] border-[var(--danger-soft)]',
      iconBg: 'bg-[var(--danger-soft)] text-[var(--danger)]',
      bar: 'bg-[var(--danger)]'
    },
    PASS: {
      bg: 'bg-[var(--surface)] border-[var(--success-soft)]',
      iconBg: 'bg-[var(--success-soft)] text-[var(--success)]',
      bar: 'bg-[var(--success)]'
    },
    REVIEW: {
      bg: 'bg-[var(--surface)] border-[var(--warning-soft)]',
      iconBg: 'bg-[var(--warning-soft)] text-[var(--warning)]',
      bar: 'bg-[var(--warning)]'
    }
  };

  const theme = colors[result.status as keyof typeof colors] || colors.REVIEW;

  return (
    <article className={`rounded-xl border ${theme.bg} shadow-sm overflow-hidden relative`}>
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${theme.bar}`}></div>
      <div className="p-5 pl-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 gap-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${theme.iconBg}`}>
              <Icon size={20} />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <p className="font-mono text-xs font-bold text-[var(--text)]">{result.rule_id}</p>
                <span className="rounded bg-[var(--surface-raised)] px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-[var(--text-faint)]">
                  {result.severity}
                </span>
              </div>
              <h4 className="text-base font-bold text-[var(--text)]">{result.rule_name}</h4>
              <p className="mt-1 text-sm text-[var(--text-muted)] leading-relaxed max-w-lg">{result.message}</p>
            </div>
          </div>
          <StatusBadge value={result.status} />
        </div>
        
        <div className="mt-5 grid gap-4 bg-[var(--surface-raised)] border border-[var(--line)] rounded-lg p-4 sm:grid-cols-2">
          <FindingValue label="Expected / Required" value={result.expected} />
          <FindingValue label={result.field ? `Extracted Data: ${result.field}` : 'Extracted Data'} value={result.actual || 'Not detected'} />
        </div>
        
        {result.evidence && (
          <div className="mt-4">
            <EvidenceViewer evidence={result.evidence} imageUrl={imageUrl} status={result.status} />
          </div>
        )}
        
        <div className="mt-4 flex items-center gap-1.5 border-t border-[var(--line)] pt-3">
          <FileSearch size={14} className="text-[var(--text-faint)]" />
          <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">Rule Reference: {result.source_reference || 'Not provided'}</p>
        </div>
      </div>
    </article>
  );
}

function FindingValue({ label, value }: { label: string; value: string }) { 
  return (
    <div className="bg-[var(--surface)] rounded border border-[var(--line)] p-3">
      <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">{label}</p>
      <p className="mt-1.5 break-words font-mono text-sm font-semibold text-[var(--text)]">{value}</p>
    </div>
  ); 
}
