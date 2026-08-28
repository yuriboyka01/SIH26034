import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, Info, Loader2 } from 'lucide-react';

type ButtonVariant = 'primary' | 'secondary' | 'danger';

export function Button({ variant = 'primary', className = '', children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return <button className={`ui-button-${variant} ${className}`} {...props}>{children}</button>;
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
  return <span className={statusClasses[normalised] || 'status-neutral'}>{label || normalised.replaceAll('_', ' ')}</span>;
}

export function SectionHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <header className="flex flex-wrap items-start justify-between gap-3 border-b border-[var(--line)] px-5 py-4">
    <div>
      {eyebrow && <p className="app-kicker mb-1">{eyebrow}</p>}
      <h3 className="section-title">{title}</h3>
      {description && <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">{description}</p>}
    </div>
    {action}
  </header>;
}

export function Metric({ label, value, detail, tone = 'neutral' }: { label: string; value: string | number; detail?: string; tone?: 'neutral' | 'pass' | 'review' | 'fail' | 'info' }) {
  const line = { neutral: 'border-[var(--line)]', pass: 'border-l-[var(--success)]', review: 'border-l-[var(--warning)]', fail: 'border-l-[var(--danger)]', info: 'border-l-[var(--info)]' }[tone];
  return <article className={`border-l-2 bg-[var(--surface)] px-4 py-4 ${line}`}>
    <p className="metric-label">{label}</p>
    <p className="metric-value mt-3">{value}</p>
    {detail && <p className="mt-2 text-xs leading-relaxed text-[var(--text-muted)]">{detail}</p>}
  </article>;
}

export function Alert({ tone = 'info', children }: { tone?: 'info' | 'error' | 'success'; children: ReactNode }) {
  const Icon = tone === 'error' ? AlertTriangle : tone === 'success' ? CheckCircle2 : Info;
  return <div className={`ui-alert ui-alert-${tone}`} role="alert"><Icon size={17} className="mt-0.5 shrink-0" />{children}</div>;
}

export function EmptyState({ icon, title, description, action }: { icon: ReactNode; title: string; description: string; action?: ReactNode }) {
  return <div className="app-surface flex min-h-56 flex-col items-center justify-center p-8 text-center">
    <div className="text-[var(--text-faint)]">{icon}</div><p className="mt-4 text-sm font-semibold text-[var(--text)]">{title}</p>
    <p className="mt-1 max-w-sm text-sm leading-relaxed text-[var(--text-muted)]">{description}</p>{action && <div className="mt-4">{action}</div>}
  </div>;
}

export function Skeleton({ className = '' }: { className?: string }) { return <div className={`ui-skeleton ${className}`} aria-hidden="true" />; }

export function ProgressStages({ stages, activeIndex, completeThrough = -1 }: { stages: string[]; activeIndex?: number; completeThrough?: number }) {
  return <ol className="grid gap-3 sm:grid-flow-col sm:auto-cols-fr sm:gap-0">
    {stages.map((stage, index) => <li key={stage} className="relative sm:after:absolute sm:after:left-3 sm:after:top-[5px] sm:after:h-px sm:after:w-[calc(100%-12px)] sm:after:bg-[var(--line)] sm:last:after:hidden">
      <span className="workflow-stage relative z-10" data-state={index <= completeThrough ? 'complete' : index === activeIndex ? 'active' : 'pending'}>{stage}</span>
    </li>)}
  </ol>;
}

export function LoadingState({ label = 'Loading workspace data' }: { label?: string }) {
  return <div className="app-surface flex min-h-64 items-center justify-center gap-3 p-8 text-sm text-[var(--text-muted)]"><Loader2 size={19} className="animate-spin text-[var(--info)]" />{label}</div>;
}
