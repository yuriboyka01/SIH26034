import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, Info, Loader2 } from 'lucide-react';

type ButtonVariant = 'primary' | 'secondary' | 'danger';

export function Button({ variant = 'primary', className = '', children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return <button className={`neo-button-${variant} ${className}`} {...props}>{children}</button>;
}

const statusClasses: Record<string, string> = {
  PASS: 'status-pass', COMPLIANT: 'status-pass', COMPLETED: 'status-pass', COMPLETE: 'status-pass', DETECTED: 'status-pass',
  FAIL: 'status-fail', VIOLATION: 'status-fail', NEEDS_REVIEW: 'status-fail', ERROR: 'status-fail',
  REVIEW: 'status-review', IMAGES_UPLOADED: 'status-review', UNCERTAIN: 'status-review',
  PROCESSING: 'status-processing', CREATED: 'status-info', ACTIVE: 'status-info',
  NOT_ANALYSED: 'status-neutral', NOT_APPLICABLE: 'status-neutral', NOT_DETECTED: 'status-neutral', PENDING: 'status-neutral',
};

export function StatusBadge({ value, label }: { value?: string | null; label?: string }) {
  const normalised = (value || 'PENDING').toUpperCase();
  return <span className={`status-badge ${statusClasses[normalised] || 'status-neutral'}`}>{label || normalised.replaceAll('_', ' ')}</span>;
}

export function SectionHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--line)] px-6 py-5">
      <div>
        {eyebrow && <p className="text-kicker mb-1.5">{eyebrow}</p>}
        <h3 className="heading-section">{title}</h3>
        {description && <p className="mt-1.5 text-sm leading-relaxed text-[var(--text-muted)]">{description}</p>}
      </div>
      {action && <div className="mt-1">{action}</div>}
    </header>
  );
}

export function Metric({ label, value, detail, tone = 'neutral' }: { label: string; value: string | number; detail?: string; tone?: 'neutral' | 'pass' | 'review' | 'fail' | 'info' }) {
  const tones = { 
    neutral: 'text-[var(--text)]', 
    pass: 'text-[var(--success)]', 
    review: 'text-[var(--warning)]', 
    fail: 'text-[var(--danger)]', 
    info: 'text-[var(--brand)]' 
  };
  return (
    <article className="bg-[var(--surface)] px-6 py-6 border-r border-[var(--line)] last:border-r-0">
      <p className="text-kicker">{label}</p>
      <p className={`heading-page mt-3 ${tones[tone]}`}>{value}</p>
      {detail && <p className="mt-2 text-sm text-[var(--text-faint)]">{detail}</p>}
    </article>
  );
}

export function Alert({ tone = 'info', children }: { tone?: 'info' | 'error' | 'success'; children: ReactNode }) {
  const Icon = tone === 'error' ? AlertTriangle : tone === 'success' ? CheckCircle2 : Info;
  const classes = {
    error: 'bg-[var(--danger-soft)] border-[var(--danger-soft)] text-[var(--danger-text)]',
    success: 'bg-[var(--success-soft)] border-[var(--success-soft)] text-[var(--success-text)]',
    info: 'bg-[var(--brand-soft)] border-[var(--brand-soft)] text-[var(--brand)]'
  };
  return (
    <div className={`flex items-start gap-3 p-4 rounded-xl border ${classes[tone]}`} role="alert">
      <Icon size={18} className="mt-0.5 shrink-0" />
      <div className="text-sm font-medium leading-relaxed">{children}</div>
    </div>
  );
}

export function EmptyState({ icon, title, description, action }: { icon: ReactNode; title: string; description: string; action?: ReactNode }) {
  return (
    <div className="flex min-h-[300px] flex-col items-center justify-center p-10 text-center bg-[var(--surface-raised)] rounded-2xl border border-dashed border-[var(--line-strong)]">
      <div className="text-[var(--text-faint)] bg-[var(--surface)] p-4 rounded-full shadow-sm border border-[var(--line)] mb-5">
        {icon}
      </div>
      <p className="text-lg font-semibold text-[var(--text)]">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-[var(--text-muted)]">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

export function Skeleton({ className = '' }: { className?: string }) { 
  return <div className={`animate-pulse bg-[var(--line)] rounded-md ${className}`} aria-hidden="true" />; 
}

export function ProgressStages({ stages, activeIndex = 0, completeThrough = -1 }: { stages: string[]; activeIndex?: number; completeThrough?: number }) {
  return (
    <div className="evidence-timeline w-full">
      {stages.map((stage, index) => {
        const isComplete = index <= completeThrough;
        const isActive = index === activeIndex;
        let status = 'pending';
        if (isComplete) status = 'complete';
        if (isActive && !isComplete) status = 'active';
        
        return (
          <div key={stage} className="timeline-node" data-status={status}>
            <div className="timeline-dot">
              {isComplete ? <CheckCircle2 size={14} className="text-white" strokeWidth={3} /> : <span className="text-[10px] font-bold">{index + 1}</span>}
            </div>
            <span className="timeline-label">{stage}</span>
          </div>
        );
      })}
    </div>
  );
}

export function LoadingState({ label = 'Loading workspace data' }: { label?: string }) {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-[var(--text-muted)] bg-[var(--canvas)]">
      <div className="relative mb-6">
        <Loader2 size={32} className="animate-spin text-[var(--brand)]" />
      </div>
      <p className="text-sm font-medium tracking-wide">{label}</p>
    </div>
  );
}
