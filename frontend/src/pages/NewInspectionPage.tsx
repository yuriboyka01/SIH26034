import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Loader2, Package, Tag, ShieldCheck } from 'lucide-react';
import { createInspection } from '../api/inspections';
import { Alert, ProgressStages } from '../components/ui';

export default function NewInspectionPage() {
  const [productName, setProductName] = useState(''); 
  const [brand, setBrand] = useState(''); 
  const [error, setError] = useState(''); 
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  
  const submit = async (event: React.FormEvent) => { 
    event.preventDefault(); 
    setError(''); 
    setLoading(true); 
    try { 
      const inspection = await createInspection({ product_name: productName, brand }); 
      navigate(`/inspections/${inspection.id}`); 
    } catch (err: any) { 
      setError(err?.response?.data?.error?.message || 'The inspection could not be created. Please try again.'); 
    } finally { 
      setLoading(false); 
    } 
  };
  
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <button className="inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--text-muted)] hover:text-[var(--brand)] transition-colors" onClick={() => navigate('/inspections')}>
        <ArrowLeft size={16} /> Back to register
      </button>
      
      <header className="mb-2">
        <p className="text-kicker text-[var(--brand)] mb-2 flex items-center gap-2">
           <ShieldCheck size={14} /> Step 1 of 3 · Case Intake
        </p>
        <h2 className="heading-page">Open an evidence record.</h2>
        <p className="text-body mt-3 max-w-2xl">Record the packaged product details first. Evidence uploading and AI compliance analysis will continue in the dedicated inspection workspace.</p>
      </header>
      
      <section className="depth-2 overflow-hidden relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-[var(--brand)]"></div>
        <div className="border-b border-[var(--line)] bg-[var(--surface-pale)] px-8 py-6">
          <ProgressStages stages={['Case Details', 'Evidence Upload', 'Analysis & Decision']} activeIndex={0} />
        </div>
        
        <div className="p-8 md:p-12">
          {error && <div className="mb-8"><Alert tone="error">{error}</Alert></div>}
          
          <div className="mb-8">
            <h3 className="heading-section">Product identification</h3>
            <p className="mt-1 text-sm text-[var(--text-muted)]">Use the declaration printed on the product package wherever possible.</p>
          </div>
          
          <form className="space-y-8" onSubmit={submit}>
            <div className="grid gap-8 md:grid-cols-2">
              <div>
                <label className="text-sm font-semibold text-[var(--text)] block mb-2" htmlFor="productName">Product name <span className="text-[var(--danger)]">*</span></label>
                <div className="relative">
                  <Package className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" size={18} />
                  <input className="neo-input pl-12" id="productName" value={productName} onChange={(event) => setProductName(event.target.value)} required placeholder="e.g. Packaged Basmati Rice, 5 kg" />
                </div>
                <p className="mt-2 text-[11px] font-medium text-[var(--text-faint)]">This label identifies the inspection throughout the workspace.</p>
              </div>
              
              <div>
                <label className="text-sm font-semibold text-[var(--text)] block mb-2" htmlFor="brand">Brand <span className="text-[var(--danger)]">*</span></label>
                <div className="relative">
                  <Tag className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" size={18} />
                  <input className="neo-input pl-12" id="brand" value={brand} onChange={(event) => setBrand(event.target.value)} required placeholder="e.g. India Gate" />
                </div>
              </div>
            </div>
            
            <div className="flex flex-col-reverse gap-4 border-t border-[var(--line)] pt-8 sm:flex-row sm:justify-end">
              <button type="button" className="neo-button-secondary" onClick={() => navigate('/inspections')}>Cancel intake</button>
              <button className="neo-button-primary shadow-lg shadow-[var(--brand-soft)]" type="submit" disabled={loading}>
                {loading ? (
                  <><Loader2 size={18} className="animate-spin" /> Creating record…</>
                ) : (
                  <>Continue to evidence upload <ArrowRight size={18} /></>
                )}
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}
