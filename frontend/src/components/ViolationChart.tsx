import { ViolationSummaryItem } from '../api/dashboard';

interface Props {
  violations: ViolationSummaryItem[];
}

export default function ViolationChart({ violations }: Props) {
  if (!violations || violations.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
        No violations found.
      </div>
    );
  }

  const maxCount = Math.max(...violations.map((v) => v.count));

  return (
    <div className="space-y-4">
      {violations.map((violation) => {
        const percentage = Math.max((violation.count / maxCount) * 100, 2);
        
        return (
          <div key={violation.rule_id} className="relative">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="font-medium text-slate-200">
                {violation.rule_id}: {violation.rule_name}
              </span>
              <span className="font-bold text-red-400">{violation.count}</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-red-500 to-rose-400 h-2 rounded-full"
                style={{ width: `${percentage}%` }}
              ></div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
