import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertCircle, ArrowLeft, Download, FileText, ImageIcon, Loader2, RefreshCw, ScanText, Trash2, Upload, X, ShieldCheck, Box } from 'lucide-react';
import { deleteInspectionImage, getInspection, uploadInspectionImage, type Inspection, type InspectionImage } from '../api/inspections';
import { analyzeInspection, getAnalysisResults, type AnalysisResponse } from '../api/analysis';
import { getProductInfo, type ProductInfo } from '../api/product_info';
import { getComplianceReports, runComplianceAnalysis, type ComplianceReport } from '../api/compliance';
import { downloadReport } from '../api/reports';
import OCRResultsPanel from '../components/OCRResultsPanel';
import ProductInfoPanel from '../components/ProductInfoPanel';
import { ComplianceResultsPanel } from '../components/ComplianceResultsPanel';
import { Alert, EmptyState, LoadingState, ProgressStages, SectionHeader, StatusBadge } from '../components/ui';

type AnalysisPhase = 'idle' | 'ocr' | 'extraction' | 'rules';

export default function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [inspection, setInspection] = useState<Inspection | null>(null); 
  const [loading, setLoading] = useState(true); 
  const [error, setError] = useState(''); 
  const [success, setSuccess] = useState('');
  const [uploading, setUploading] = useState(false); 
  const [uploadProgress, setUploadProgress] = useState(0); 
  const [dragOver, setDragOver] = useState(false); 
  const [deleteCandidate, setDeleteCandidate] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null); 
  const [productInfo, setProductInfo] = useState<ProductInfo | null>(null); 
  const [complianceReports, setComplianceReports] = useState<ComplianceReport[]>([]); 
  const [analysing, setAnalysing] = useState(false); 
  const [analysisPhase, setAnalysisPhase] = useState<AnalysisPhase>('idle'); 
  const [analysisProgress, setAnalysisProgress] = useState(0); 
  const [processedImageCount, setProcessedImageCount] = useState(0); 
  const [analysisError, setAnalysisError] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchInspection = useCallback(async () => { 
    if (!id) return; 
    try { 
      const [record, info, compliance] = await Promise.all([
        getInspection(id), 
        getProductInfo(id).catch(() => null), 
        getComplianceReports(id).catch(() => null)
      ]); 
      setInspection(record); 
      setProductInfo(info?.product_info_list?.[0] || null); 
      setComplianceReports(compliance?.reports || []); 
    } catch { 
      setError('The inspection record could not be loaded. Please return to the register and try again.'); 
    } finally { 
      setLoading(false); 
    } 
  }, [id]);

  useEffect(() => { 
    fetchInspection(); 
    if (id) getAnalysisResults(id).then(setAnalysisResult).catch(() => undefined); 
  }, [fetchInspection, id]);

  const flash = (message: string) => { setSuccess(message); window.setTimeout(() => setSuccess(''), 3000); };
  
  const handleFileUpload = async (files: FileList | null) => { 
    if (!files?.length || !id) return; 
    setError(''); setUploading(true); setUploadProgress(0); 
    try { 
      for (const file of Array.from(files)) { 
        if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { setError(`${file.name}: only JPG, PNG, and WEBP evidence is supported.`); continue; } 
        if (file.size > 10 * 1024 * 1024) { setError(`${file.name}: file size exceeds the 10 MB limit.`); continue; } 
        await uploadInspectionImage(id, file, 'OTHER', setUploadProgress); 
      } 
      await fetchInspection(); 
      flash('Evidence uploaded. Run analysis when the evidence set is ready.'); 
    } catch (err: unknown) { 
      const detail = err as { response?: { data?: { error?: { message?: string } } } }; 
      setError(detail.response?.data?.error?.message || 'Evidence could not be uploaded. Please try again.'); 
    } finally { 
      setUploading(false); setUploadProgress(0); 
      if (fileInputRef.current) fileInputRef.current.value = ''; 
    } 
  };
  
  const confirmDelete = async () => { 
    if (!id || !deleteCandidate) return; 
    try { 
      await deleteInspectionImage(id, deleteCandidate); setDeleteCandidate(null); setAnalysisResult(null); await fetchInspection(); flash('Evidence image deleted.'); 
    } catch (err: unknown) { 
      const detail = err as { response?: { data?: { error?: { message?: string } } } }; 
      setError(detail.response?.data?.error?.message || 'Evidence could not be deleted.'); 
    } 
  };
  
  const handleAnalyze = async () => {
    if (!id) return;
    setAnalysisError(''); setAnalysing(true); setAnalysisPhase('ocr'); setAnalysisProgress(12); setProcessedImageCount(0);
    let progressTimer: number | undefined;
    try {
      progressTimer = window.setInterval(() => setAnalysisProgress((progress) => Math.min(progress + 3, 68)), 900);
      const analysis = await analyzeInspection(id);
      window.clearInterval(progressTimer); progressTimer = undefined;
      setAnalysisResult(analysis); setProcessedImageCount(analysis.images.length); setAnalysisPhase('extraction'); setAnalysisProgress(74);
      const info = await getProductInfo(id);
      setProductInfo(info.product_info_list?.[0] || null); setAnalysisPhase('rules'); setAnalysisProgress(88);
      const compliance = await runComplianceAnalysis(id);
      setComplianceReports(compliance.reports || []); setAnalysisProgress(100);
      await fetchInspection(); flash('Evidence analysis and rule evaluation completed.');
    } catch (err: unknown) {
      const detail = err as { response?: { data?: { error?: { message?: string } } } };
      setAnalysisError(detail.response?.data?.error?.message || 'Analysis could not be completed. Review the evidence and try again.');
    } finally {
      if (progressTimer) window.clearInterval(progressTimer);
      setAnalysing(false); setAnalysisPhase('idle');
    }
  };

  if (loading) return <LoadingState label="Opening inspection workspace" />;
  if (!inspection) return <EmptyState icon={<AlertCircle size={28} />} title="Inspection unavailable" description="The requested inspection could not be found or loaded." action={<Link to="/inspections" className="neo-button-secondary">Back to register</Link>} />;

  const hasImages = inspection.images.length > 0;
  const hasSuccessfulAnalysis = analysisResult?.images.some((result) => result.status === 'OK') || false;
  const hasReports = complianceReports.length > 0;
  
  const phaseIndex: Record<AnalysisPhase, number> = { idle: 0, ocr: 1, extraction: 2, rules: 3 };
  const phaseCompleteThrough: Record<AnalysisPhase, number> = { idle: -1, ocr: 0, extraction: 1, rules: 2 };
  
  const stages = ['Evidence Upload', 'OCR Extraction', 'AI Intelligence', 'Rule Evaluation', 'Inspector Decision']; 
  const activeIndex = analysing ? phaseIndex[analysisPhase] : !hasImages ? 0 : hasReports ? 4 : hasSuccessfulAnalysis ? 3 : 1; 
  const completeThrough = analysing ? phaseCompleteThrough[analysisPhase] : hasReports ? 4 : hasSuccessfulAnalysis ? 2 : hasImages ? 0 : -1;

  return (
    <div className="space-y-6 max-w-[1920px] mx-auto">
      <Link to="/inspections" className="inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--text-muted)] hover:text-[var(--brand)] transition-colors">
        <ArrowLeft size={16} /> Back to inspection register
      </Link>
      
      <section className="depth-1 overflow-hidden relative">
        <div className="flex flex-wrap items-center justify-between gap-6 px-8 py-8">
          <div>
            <p className="text-kicker mb-2 flex items-center gap-2">
              <ShieldCheck size={14} className="text-[var(--brand)]" />
              Inspection <span className="text-[var(--line-strong)] mx-1">•</span> {inspection.inspection_number}
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <h2 className="heading-page">{inspection.product_name}</h2>
              <StatusBadge value={inspection.status} />
            </div>
            <p className="mt-3 text-sm text-[var(--text-muted)] flex items-center gap-2">
              <Box size={14} className="text-[var(--text-faint)]" /> {inspection.brand} 
              <span className="text-[var(--line-strong)] mx-1">•</span> 
              <span className="font-mono text-xs">Opened {new Date(inspection.created_at).toLocaleString()}</span>
            </p>
          </div>
          
          <div className="flex flex-wrap gap-3">
            {hasReports && (
              <>
                <button onClick={() => downloadReport(id!, 'pdf')} className="neo-button-secondary">
                  <FileText size={16} className="text-[var(--danger)]" /> PDF
                </button>
                <button onClick={() => downloadReport(id!, 'docx')} className="neo-button-secondary">
                  <Download size={16} className="text-[var(--brand)]" /> DOCX
                </button>
              </>
            )}
            {hasImages && (
              <button onClick={handleAnalyze} disabled={analysing} className="neo-button-primary shadow-lg shadow-[var(--brand-soft)]">
                {analysing ? (
                  <><Loader2 size={16} className="animate-spin" /> Analysing evidence…</>
                ) : hasSuccessfulAnalysis ? (
                  <><RefreshCw size={16} /> Re-run analysis</>
                ) : (
                  <><ScanText size={16} /> Analyze evidence</>
                )}
              </button>
            )}
          </div>
        </div>
        
        <div className="border-t border-[var(--line)] bg-[var(--surface-raised)] px-8 py-5">
          <ProgressStages stages={stages} activeIndex={activeIndex} completeThrough={completeThrough} />
        </div>
      </section>

      {error && <Alert tone="error">{error}<button aria-label="Dismiss" className="ml-auto -mr-1 text-current" onClick={() => setError('')}><X size={16} /></button></Alert>}
      {analysisError && <Alert tone="error">{analysisError}<button aria-label="Dismiss" className="ml-auto -mr-1 text-current" onClick={() => setAnalysisError('')}><X size={16} /></button></Alert>}
      {success && <Alert tone="success">{success}</Alert>}
      
      {analysing && <AnalysisProgress phase={analysisPhase} progress={analysisProgress} imageCount={inspection.images.length} processedImageCount={processedImageCount} />}
      
      {/* 3-Column Layout */}
      <section className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
        {/* LEFT COLUMN: EVIDENCE */}
        <div className="space-y-6 flex flex-col">
          <section className="depth-2 overflow-hidden">
            <SectionHeader eyebrow="01 / Evidence" title="Evidence capture" description="Upload package images to establish the inspection record." />
            <div className="p-5">
              <div 
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} 
                onDragLeave={() => setDragOver(false)} 
                onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFileUpload(e.dataTransfer.files); }} 
                onClick={() => fileInputRef.current?.click()} 
                className={`cursor-pointer border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                  dragOver ? 'border-[var(--brand)] bg-[var(--brand-soft)] scale-[1.02]' : 'border-[var(--line-strong)] bg-[var(--surface-raised)] hover:border-[var(--brand)]'
                }`}
              >
                {uploading ? (
                  <div>
                    <Loader2 size={32} className="mx-auto animate-spin text-[var(--brand)]" />
                    <p className="mt-4 text-sm font-semibold text-[var(--text)]">Uploading evidence · {uploadProgress}%</p>
                    <div className="mx-auto mt-4 h-1.5 w-48 overflow-hidden rounded-full bg-[var(--line)]">
                      <div className="h-full bg-[var(--brand)] transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="w-14 h-14 bg-[var(--surface)] border border-[var(--line-strong)] rounded-2xl mx-auto flex items-center justify-center shadow-sm">
                      <Upload size={24} className="text-[var(--brand)]" />
                    </div>
                    <p className="mt-4 text-sm font-bold text-[var(--text)]">Add package evidence</p>
                    <p className="mt-1 text-xs text-[var(--text-muted)]">Drop JPG, PNG, or WEBP files here<br/>Max 10 MB per image</p>
                  </>
                )}
                <input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp" multiple className="hidden" onChange={(e) => handleFileUpload(e.target.files)} />
              </div>
            </div>
          </section>
          
          {hasImages ? (
            <div className="space-y-6 flex-1">
              {inspection.images.map((image) => (
                <EvidenceItem 
                  key={image.id} 
                  image={image} 
                  result={analysisResult?.images.find((r) => r.image_id === image.id) || null} 
                  pendingDelete={deleteCandidate === image.id} 
                  onAskDelete={() => setDeleteCandidate(image.id)} 
                  onCancelDelete={() => setDeleteCandidate(null)} 
                  onConfirmDelete={confirmDelete} 
                />
              ))}
            </div>
          ) : (
            <div className="flex-1">
              <EmptyState icon={<ImageIcon size={32} />} title="No evidence attached" description="Upload a package image to begin OCR extraction and compliance analysis." />
            </div>
          )}
        </div>

        {/* CENTER COLUMN: EXTRACTION */}
        <div className="space-y-6 flex flex-col">
          <ProductInfoPanel productInfo={productInfo} />
        </div>

        {/* RIGHT COLUMN: RULES */}
        <div className="space-y-6 flex flex-col">
          <ComplianceResultsPanel reports={complianceReports} isAnalyzing={analysing} images={inspection.images.map((image) => ({ id: image.id, url: image.url }))} />
          
          {hasReports && (
            <section className="depth-2 overflow-hidden">
              <SectionHeader eyebrow="04 / Report" title="Official report ready" description="Download the official evidence-linked report." />
              <div className="flex flex-col gap-3 p-5">
                <button onClick={() => downloadReport(id!, 'pdf')} className="neo-button-secondary w-full justify-between">
                  <span className="flex items-center gap-2"><FileText size={16} className="text-[var(--danger)]" /> Download PDF</span>
                  <Download size={16} className="text-[var(--text-faint)]" />
                </button>
                <button onClick={() => downloadReport(id!, 'docx')} className="neo-button-secondary w-full justify-between">
                  <span className="flex items-center gap-2"><FileText size={16} className="text-[var(--brand)]" /> Download DOCX</span>
                  <Download size={16} className="text-[var(--text-faint)]" />
                </button>
              </div>
            </section>
          )}
        </div>
      </section>
    </div>
  );
}

function AnalysisProgress({ phase, progress, imageCount, processedImageCount }: { phase: AnalysisPhase; progress: number; imageCount: number; processedImageCount: number }) {
  const phaseCopy: Record<Exclude<AnalysisPhase, 'idle'>, { title: string; description: string }> = {
    ocr: { title: 'Reading package evidence', description: `Running image-quality checks and OCR for ${imageCount} uploaded ${imageCount === 1 ? 'image' : 'images'}.` },
    extraction: { title: 'Extracting package declarations', description: 'Saving the text and matching label details to their source evidence.' },
    rules: { title: 'Evaluating compliance rules', description: 'Checking extracted declarations against the applicable legal-metrology rules.' },
  };
  const current = phaseCopy[phase === 'idle' ? 'ocr' : phase];
  const steps: Array<{ phase: Exclude<AnalysisPhase, 'idle'>; label: string }> = [{ phase: 'ocr', label: 'OCR & Image Quality' }, { phase: 'extraction', label: 'AI Extraction' }, { phase: 'rules', label: 'Rule Evaluation' }];
  const order: Record<AnalysisPhase, number> = { idle: 0, ocr: 1, extraction: 2, rules: 3 };
  
  return (
    <section className="depth-2 overflow-hidden border-[var(--brand)] border-2 shadow-[0_0_20px_rgba(37,99,235,0.1)]" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-5 bg-[var(--surface-pale)]">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[var(--surface)] shadow-sm flex items-center justify-center">
             <Loader2 size={24} className="animate-spin text-[var(--brand)]" />
          </div>
          <div>
            <p className="text-lg font-bold text-[var(--text)]">{current.title}</p>
            <p className="mt-0.5 text-sm text-[var(--text-muted)]">{current.description}</p>
          </div>
        </div>
        <div className="text-right">
          <span className="block font-mono text-xl font-bold text-[var(--brand)]">{progress}%</span>
          <span className="font-mono text-[11px] font-semibold text-[var(--text-faint)] uppercase tracking-wider">{processedImageCount} / {imageCount} processed</span>
        </div>
      </div>
      <div className="h-1.5 bg-[var(--line)]">
        <div className="h-full bg-gradient-to-r from-[var(--brand)] to-[var(--info)] transition-[width] duration-500" style={{ width: `${progress}%` }} />
      </div>
      <div className="px-6 py-4 bg-[var(--surface)]">
         <ol className="flex justify-between items-center text-sm font-semibold">
           {steps.map((step, idx) => (
             <li key={step.phase} className={`flex items-center gap-2 flex-1 ${idx !== 0 ? 'justify-center' : ''} ${idx === 2 ? 'justify-end' : ''} ${order[step.phase] < order[phase] ? 'text-[var(--success)]' : step.phase === phase ? 'text-[var(--brand)]' : 'text-[var(--text-faint)]'}`}>
               <span className={`grid h-6 w-6 place-items-center rounded-full border-2 text-[10px] ${order[step.phase] < order[phase] ? 'border-[var(--success)] bg-[var(--success-soft)]' : step.phase === phase ? 'border-[var(--brand)] bg-[var(--brand-soft)]' : 'border-[var(--line-strong)]'}`}>
                 {order[step.phase] < order[phase] ? '✓' : order[step.phase]}
               </span>
               {step.label}
             </li>
           ))}
         </ol>
      </div>
    </section>
  );
}

function EvidenceItem({ image, result, pendingDelete, onAskDelete, onCancelDelete, onConfirmDelete }: { image: InspectionImage; result: AnalysisResponse['images'][number] | null; pendingDelete: boolean; onAskDelete: () => void; onCancelDelete: () => void; onConfirmDelete: () => void }) {
  return (
    <section className="depth-2 overflow-hidden h-full flex flex-col">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] px-5 py-4 bg-[var(--surface-raised)]">
        <div className="min-w-0">
          <p className="truncate text-sm font-bold text-[var(--text)]" title={image.original_filename}>{image.original_filename}</p>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-[var(--text-faint)]">
            {image.image_type} <span className="mx-1">•</span> {(image.file_size / 1024).toFixed(0)} KB
          </p>
        </div>
        {pendingDelete ? (
          <div className="flex items-center gap-2 bg-[var(--danger-soft)] px-3 py-1.5 rounded-lg border border-[var(--danger-soft)]">
            <span className="text-xs font-semibold text-[var(--danger)]">Remove?</span>
            <button className="neo-button-danger !min-h-7 !px-3 !py-1 !text-xs shadow-none" onClick={onConfirmDelete}>Confirm</button>
            <button className="ui-icon-button !w-7 !h-7 bg-[var(--surface)]" onClick={onCancelDelete} aria-label="Cancel"><X size={14} /></button>
          </div>
        ) : (
          <button className="ui-icon-button bg-[var(--surface)] shadow-sm border border-[var(--line)] hover:!text-[var(--danger)] hover:!border-[var(--danger-soft)]" onClick={onAskDelete} aria-label={`Delete ${image.original_filename}`}>
            <Trash2 size={16} />
          </button>
        )}
      </header>
      <div className="p-5 flex-1 flex flex-col">
        {result ? (
          <OCRResultsPanel imageUrl={image.url} result={result} />
        ) : (
          <div className="overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] flex-1 flex flex-col group relative">
            {/* Soft inner shadow for premium image feel */}
            <div className="absolute inset-0 shadow-[inset_0_0_20px_rgba(0,0,0,0.02)] pointer-events-none z-10 rounded-xl"></div>
            <img src={image.url} alt={image.original_filename} className="w-full h-auto object-contain flex-1 max-h-[400px]" loading="lazy" />
            <div className="border-t border-[var(--line)] bg-[var(--surface)]/80 backdrop-blur-sm px-5 py-4 z-20">
              <p className="text-sm font-bold text-[var(--text)]">Evidence ready</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">Run analysis to extract declarations.</p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
