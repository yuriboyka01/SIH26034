import { Box } from 'lucide-react';
import type { ProductInfo } from '../api/product_info';
import { SectionHeader } from './ui';

const priorityFields: Record<string, { label: string; required: boolean }> = {
  product_name: { label: 'Product name', required: true }, 
  manufacturer: { label: 'Manufacturer / Packer', required: true }, 
  net_quantity: { label: 'Net quantity', required: true }, 
  mrp: { label: 'MRP', required: true }, 
  manufacturing_date: { label: 'Mfg / Packing date', required: true }, 
  country_of_origin: { label: 'Country of origin', required: true }, 
  customer_care: { label: 'Consumer Contact', required: true }, 
};

export default function ProductInfoPanel({ productInfo }: { productInfo: ProductInfo | null }) {
  if (!productInfo) {
    return (
      <section className="depth-2 overflow-hidden flex flex-col">
        <SectionHeader eyebrow="03" title="Product Snapshot" description="Awaiting evidence analysis." />
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center bg-[var(--canvas)] rounded-xl border border-dashed border-[var(--line-strong)]">
          <div className="w-12 h-12 bg-[var(--surface)] rounded-full shadow-sm border border-[var(--line)] flex items-center justify-center mb-4">
            <Box size={20} className="text-[var(--text-faint)]" />
          </div>
          <p className="text-sm font-bold text-[var(--text)]">Snapshot pending</p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">Extracted info will appear here.</p>
        </div>
      </section>
    );
  }

  const fieldMap = Object.fromEntries(productInfo.fields.map((field) => [field.field_name, field]));
  const rows = Object.entries(priorityFields).map(([key, meta]) => ({ key, meta, value: fieldMap[key] }));

  return (
    <section className="depth-2 overflow-hidden flex flex-col">
      <SectionHeader eyebrow="03" title="Product Snapshot" description="Key extracted declarations" />
      
      <div className="bg-[var(--surface-raised)] p-4 flex-1">
        <div className="grid gap-3 sm:grid-cols-2">
          {rows.map(({ key, meta, value }) => {
            const isDetected = value?.detection_status === 'DETECTED';
            
            return (
              <div key={key} className="bg-[var(--surface)] rounded-lg border border-[var(--line)] p-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">
                  {meta.label}
                </p>
                <div className="mt-1">
                  {isDetected ? (
                    <p className="text-sm font-bold text-[var(--text)] break-words">{value?.value}</p>
                  ) : (
                    <p className="text-sm font-medium text-[var(--text-muted)] italic">Not detected</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
