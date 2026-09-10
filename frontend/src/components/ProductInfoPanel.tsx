import { Box } from 'lucide-react';
import type { ProductInfo } from '../api/product_info';
import { SectionHeader, StatusBadge } from './ui';

const fields: Record<string, { label: string; required: boolean }> = {
  product_name: { label: 'Product name', required: true }, 
  brand_name: { label: 'Brand', required: true }, 
  manufacturer: { label: 'Manufacturer', required: true }, 
  net_quantity: { label: 'Net quantity', required: true }, 
  mrp: { label: 'MRP', required: true }, 
  manufacturing_date: { label: 'Manufacturing date', required: true }, 
  expiry_date: { label: 'Expiry / best before', required: true }, 
  batch_number: { label: 'Batch number', required: true }, 
  country_of_origin: { label: 'Country of origin', required: true }, 
  license_number: { label: 'FSSAI / licence no.', required: true }, 
  ingredients: { label: 'Ingredients', required: false }, 
  customer_care: { label: 'Customer care', required: false }, 
  warnings: { label: 'Warnings / declarations', required: false },
};

export default function ProductInfoPanel({ productInfo }: { productInfo: ProductInfo | null }) {
  if (!productInfo) {
    return (
      <section className="depth-2 overflow-hidden h-full flex flex-col">
        <SectionHeader eyebrow="02 / Intelligence" title="AI Extraction" description="Awaiting evidence analysis to populate declarations." />
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[var(--canvas)] m-4 rounded-xl border border-dashed border-[var(--line-strong)]">
          <div className="w-14 h-14 bg-[var(--surface)] rounded-full shadow-sm border border-[var(--line)] flex items-center justify-center mb-4">
            <Box size={24} className="text-[var(--text-faint)]" />
          </div>
          <p className="text-base font-bold text-[var(--text)]">Declarations pending</p>
          <p className="mt-2 max-w-xs text-sm leading-relaxed text-[var(--text-muted)]">Structured package declarations will appear here after evidence analysis is complete.</p>
        </div>
      </section>
    );
  }

  const fieldMap = Object.fromEntries(productInfo.fields.map((field) => [field.field_name, field]));
  const rows = Object.entries(fields).map(([key, meta]) => ({ key, meta, value: fieldMap[key] }));
  const detected = rows.filter((row) => row.value?.detection_status === 'DETECTED').length;

  return (
    <section className="depth-2 overflow-hidden h-full flex flex-col">
      <SectionHeader eyebrow="02 / Intelligence" title="AI Extraction" description={`${detected} of ${rows.length} configured declarations detected from evidence.`} />
      
      <div className="flex-1 overflow-y-auto bg-[var(--surface-raised)] p-4">
        <div className="space-y-3">
          {rows.map(({ key, meta, value }) => {
            const isDetected = value?.detection_status === 'DETECTED';
            const confidence = value?.evidence?.confidence;
            const confPercent = confidence != null ? Math.round(confidence * 100) : null;
            
            return (
              <div key={key} className={`bg-[var(--surface)] rounded-xl border p-4 transition-shadow hover:shadow-md ${isDetected ? 'border-[var(--line)]' : 'border-[var(--line-strong)] opacity-80'}`}>
                <div className="flex justify-between items-start mb-2">
                  <p className="text-xs font-bold uppercase tracking-wider text-[var(--text-faint)]">
                    {meta.label} {meta.required && <span className="text-[var(--danger)] ml-0.5">*</span>}
                  </p>
                  <StatusBadge value={value?.detection_status} />
                </div>
                
                <div className="mt-1">
                  {isDetected ? (
                    <p className="text-base font-bold text-[var(--text)]">{value?.value}</p>
                  ) : (
                    <p className="text-sm font-medium text-[var(--text-muted)] italic">Not detected in evidence</p>
                  )}
                </div>
                
                {isDetected && confPercent !== null && (
                  <div className="mt-3 pt-3 border-t border-[var(--line)] flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">Confidence score</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-[var(--line)] rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${confPercent >= 90 ? 'bg-[var(--success)]' : confPercent >= 70 ? 'bg-[var(--warning)]' : 'bg-[var(--danger)]'}`} 
                          style={{ width: `${confPercent}%` }}
                        />
                      </div>
                      <span className="font-mono text-xs font-bold text-[var(--text)]">{confPercent}%</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <div className="border-t border-[var(--line)] bg-[var(--surface)] px-5 py-3">
        <p className="text-[11px] font-medium text-[var(--text-faint)]">
          <span className="text-[var(--danger)] mr-1">*</span> Mandatory declaration under LM rules.
        </p>
      </div>
    </section>
  );
}
