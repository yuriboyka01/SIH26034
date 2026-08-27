/**
 * Phase 3: ProductInfoPanel — displays structured product information extracted from OCR.
 *
 * Shows a clean two-column table of detected fields, with visual indicators for
 * DETECTED / UNCERTAIN / NOT_DETECTED status. Designed for hackathon demo impact.
 */

import { type ProductInfo } from '../api/product_info';
import {
  Package,
  Tag,
  Weight,
  IndianRupee,
  Calendar,
  Hash,
  Globe,
  List,
  Shield,
  Phone,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  XCircle,
  Info,
} from 'lucide-react';

interface Props {
  productInfo: ProductInfo | null;
}

// ── Field metadata for display ────────────────────────────────────────────────

const FIELD_META: Record<
  string,
  { label: string; icon: React.ReactNode; mandatory: boolean }
> = {
  product_name: { label: 'Product Name', icon: <Package className="w-3.5 h-3.5" />, mandatory: true },
  brand_name: { label: 'Brand', icon: <Tag className="w-3.5 h-3.5" />, mandatory: true },
  manufacturer: { label: 'Manufacturer', icon: <Shield className="w-3.5 h-3.5" />, mandatory: true },
  net_quantity: { label: 'Net Quantity', icon: <Weight className="w-3.5 h-3.5" />, mandatory: true },
  mrp: { label: 'MRP (₹)', icon: <IndianRupee className="w-3.5 h-3.5" />, mandatory: true },
  manufacturing_date: { label: 'Mfg. Date', icon: <Calendar className="w-3.5 h-3.5" />, mandatory: true },
  expiry_date: { label: 'Expiry / Best Before', icon: <Calendar className="w-3.5 h-3.5" />, mandatory: true },
  batch_number: { label: 'Batch No.', icon: <Hash className="w-3.5 h-3.5" />, mandatory: true },
  country_of_origin: { label: 'Country of Origin', icon: <Globe className="w-3.5 h-3.5" />, mandatory: true },
  ingredients: { label: 'Ingredients', icon: <List className="w-3.5 h-3.5" />, mandatory: false },
  license_number: { label: 'FSSAI / Lic. No.', icon: <Shield className="w-3.5 h-3.5" />, mandatory: true },
  customer_care: { label: 'Customer Care', icon: <Phone className="w-3.5 h-3.5" />, mandatory: false },
  warnings: { label: 'Warnings / Declarations', icon: <AlertTriangle className="w-3.5 h-3.5" />, mandatory: false },
};

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  if (status === 'DETECTED') {
    return (
      <span className="inline-flex items-center gap-1 text-emerald-400">
        <CheckCircle2 className="w-3.5 h-3.5" />
      </span>
    );
  }
  if (status === 'UNCERTAIN') {
    return (
      <span className="inline-flex items-center gap-1 text-amber-400">
        <HelpCircle className="w-3.5 h-3.5" />
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-slate-500">
      <XCircle className="w-3.5 h-3.5" />
    </span>
  );
}

// ── Field row ─────────────────────────────────────────────────────────────────

function FieldRow({
  label,
  icon,
  value,
  status,
  mandatory,
}: {
  label: string;
  icon: React.ReactNode;
  value: string | null;
  status: string;
  mandatory: boolean;
}) {
  const isDetected = status === 'DETECTED' || status === 'UNCERTAIN';

  return (
    <tr className="border-b border-slate-700/40 last:border-0 hover:bg-slate-700/20 transition-colors">
      {/* Field label */}
      <td className="py-2.5 pr-4 w-44">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500">{icon}</span>
          <span className="text-xs text-slate-400 font-medium">
            {label}
            {mandatory && (
              <span className="text-red-400 ml-0.5 text-[10px]">*</span>
            )}
          </span>
        </div>
      </td>

      {/* Status indicator */}
      <td className="py-2.5 pr-3 w-8">
        <StatusBadge status={status} />
      </td>

      {/* Value */}
      <td className="py-2.5">
        {isDetected && value ? (
          <span
            className={`text-sm font-medium ${
              status === 'UNCERTAIN' ? 'text-amber-300' : 'text-white'
            }`}
          >
            {value}
            {status === 'UNCERTAIN' && (
              <span className="ml-1.5 text-xs text-amber-500/70 font-normal">(uncertain)</span>
            )}
          </span>
        ) : (
          <span className="text-xs text-slate-600 italic">Not detected</span>
        )}
      </td>
    </tr>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ProductInfoPanel({ productInfo }: Props) {
  if (!productInfo) {
    return (
      <div
        className="rounded-xl p-6 text-center"
        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
      >
        <Info className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <p className="text-sm text-slate-500">
          Product information will appear here after analysis.
        </p>
      </div>
    );
  }

  // Build field rows from the fields list (evidence-linked)
  const fieldMap = Object.fromEntries(
    productInfo.fields.map((f) => [f.field_name, f])
  );

  const mandatoryFields = Object.entries(FIELD_META).filter(([, m]) => m.mandatory);
  const optionalFields = Object.entries(FIELD_META).filter(([, m]) => !m.mandatory);

  const detectedCount = productInfo.fields.filter(
    (f) => f.detection_status === 'DETECTED'
  ).length;
  const totalMandatory = mandatoryFields.length;
  const detectedMandatory = mandatoryFields.filter(
    ([key]) => fieldMap[key]?.detection_status === 'DETECTED'
  ).length;

  return (
    <div className="space-y-4">
      {/* Header with summary */}
      <div
        className="rounded-xl p-4"
        style={{
          background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.08))',
          border: '1px solid rgba(99,102,241,0.2)',
        }}
      >
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Package className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-semibold text-white">Extracted Product Information</span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="text-slate-400">
              <span className="text-indigo-300 font-semibold">{detectedCount}</span>
              /{productInfo.fields.length} fields detected
            </span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                detectedMandatory === totalMandatory
                  ? 'bg-emerald-500/15 text-emerald-400'
                  : detectedMandatory >= Math.ceil(totalMandatory * 0.6)
                  ? 'bg-amber-500/15 text-amber-400'
                  : 'bg-red-500/15 text-red-400'
              }`}
            >
              {detectedMandatory}/{totalMandatory} mandatory
            </span>
          </div>
        </div>
        {productInfo.total_blocks_processed != null && (
          <p className="text-xs text-slate-500 mt-1.5">
            Processed {productInfo.total_blocks_processed} OCR text blocks · Extraction v{productInfo.extraction_version}
          </p>
        )}
      </div>

      {/* Mandatory Fields Table */}
      <div
        className="rounded-xl overflow-hidden"
        style={{ border: '1px solid rgba(255,255,255,0.08)' }}
      >
        <div className="px-4 py-2.5 bg-slate-800/60 border-b border-slate-700/50">
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Mandatory Declarations (Legal Metrology Rules)
          </p>
        </div>
        <div className="px-4 bg-slate-800/30">
          <table className="w-full">
            <tbody>
              {mandatoryFields.map(([key, meta]) => {
                const field = fieldMap[key];
                return (
                  <FieldRow
                    key={key}
                    label={meta.label}
                    icon={meta.icon}
                    value={field?.value ?? null}
                    status={field?.detection_status ?? 'NOT_DETECTED'}
                    mandatory={true}
                  />
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Optional Fields Table */}
      <div
        className="rounded-xl overflow-hidden"
        style={{ border: '1px solid rgba(255,255,255,0.08)' }}
      >
        <div className="px-4 py-2.5 bg-slate-800/60 border-b border-slate-700/50">
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Additional Declarations
          </p>
        </div>
        <div className="px-4 bg-slate-800/30">
          <table className="w-full">
            <tbody>
              {optionalFields.map(([key, meta]) => {
                const field = fieldMap[key];
                return (
                  <FieldRow
                    key={key}
                    label={meta.label}
                    icon={meta.icon}
                    value={field?.value ?? null}
                    status={field?.detection_status ?? 'NOT_DETECTED'}
                    mandatory={false}
                  />
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 px-1 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Detected
        </span>
        <span className="flex items-center gap-1">
          <HelpCircle className="w-3 h-3 text-amber-400" /> Uncertain
        </span>
        <span className="flex items-center gap-1">
          <XCircle className="w-3 h-3 text-slate-500" /> Not detected
        </span>
        <span className="ml-auto">
          <span className="text-red-400">*</span> Mandatory field
        </span>
      </div>
    </div>
  );
}
