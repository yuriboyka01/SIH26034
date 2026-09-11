import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { 
  AlertCircle, 
  ArrowLeft, 
  Camera, 
  Download, 
  FileText, 
  ImageIcon, 
  Loader2, 
  RefreshCw, 
  ScanText, 
  Trash2, 
  Upload, 
  X, 
  ShieldCheck, 
  Box 
} from 'lucide-react';
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
  const cameraInputRef = useRef<HTMLInputElement>(null);

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

  const flash = (message: string) => { 
    setSuccess(message); 
    window.setTimeout(() => setSuccess(''), 3000); 
  };
  
  const handleFileUpload = async (files: FileList | null) => { 
    if (!files?.length || !id) return; 
    setError(''); 
    setUploading(true); 
    setUploadProgress(0); 
    try { 
      for (const file of Array.from(files)) { 
        if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { 
          setError(`${file.name}: only JPG, PNG, and WEBP evidence is supported.`); 
          continue; 
        } 
        if (file.size > 10 * 1024 * 1024) { 
          setError(`${file.name}: file size exceeds the 10 MB limit.`); 
          continue; 
        } 
        await uploadInspectionImage(id, file, 'OTHER', setUploadProgress); 
      } 
      await fetchInspection(); 
      flash('Evidence uploaded. Run analysis when the evidence set is ready.'); 
    } catch (err: unknown) { 
      const detail = err as { response?: { data?: { error?: { message?: string } } } }; 
      setError(detail.response?.data?.error?.message || 'Evidence could not be uploaded. Please try again.'); 
    } finally { 
      setUploading(false); 
      setUploadProgress(0); 
      if (fileInputRef.current) fileInputRef.current.value = ''; 
      if (cameraInputRef.current) cameraInputRef.current.value = '';
    } 
  };
  
  const confirmDelete = async () => { 
    if (!id || !deleteCandidate) return; 
    try { 
      await deleteInspectionImage(id, deleteCandidate); 
      setDeleteCandidate(null); 
      setAnalysisResult(null); 
      await fetchInspection(); 
      flash('Evidence image deleted.'); 
    } catch (err: unknown) { 
      const detail = err as { response?: { data?: { error?: { message?: string } } } }; 
      setError(detail.response?.data?.error?.message || 'Evidence could not be deleted.'); 
    } 
  };
  
  const handleAnalyze = async () => {
    if (!id) return;
    setAnalysisError(''); 
    setAnalysing(true); 
    setAnalysisPhase('ocr'); 
    setAnalysisProgress(12); 
    setProcessedImageCount(0);
    
    let progressTimer: number | undefined;
    try {
      progressTimer = window.setInterval(() => setAnalysisProgress((progress) => Math.min(progress + 3, 68)), 900);
      const analysis = await analyzeInspection(id);
      window.clearInterval(progressTimer); 
      progressTimer = undefined;
      setAnalysisResult(analysis); 
      setProcessedImageCount(analysis.images.length); 
      setAnalysisPhase('extraction'); 
      setAnalysisProgress(74);
      
      const info = await getProductInfo(id);
      setProductInfo(info.product_info_list?.[0] || null); 
      setAnalysisPhase('rules'); 
      setAnalysisProgress(88);
      
      const compliance = await runComplianceAnalysis(id);
      setComplianceReports(compliance.reports || []); 
      setAnalysisProgress(100);
      await fetchInspection(); 
      flash('Evidence analysis and rule evaluation completed.');
    } catch (err: unknown) {
      const detail = err as { response?: { data?: { error?: { message?: string } } } };
      setAnalysisError(detail.response?.data?.error?.message || 'Analysis could not be completed. Review the evidence and try again.');
    } finally {
      if (progressTimer) window.clearInterval(progressTimer);
      setAnalysing(false); 
      setAnalysisPhase('idle');
    }
  };

  if (loading) return <LoadingState label="Opening inspection workspace" />;
  if (!inspection) return <EmptyState icon={<AlertCircle size={28} />} title="Inspection unavailable" description="The requested inspection could not be found or loaded." action={<Link to="/inspections" className="neo-button-secondary">Back to register</Link>} />;

  const hasImages = inspection.images.length > 0;
  const hasSuccessfulAnalysis = analysisResult?.images.some((result) => result.status === 'OK') || false;
  const hasReports = complianceReports.length > 0;

  const stages = ['Evidence Upload', 'OCR Extraction', 'AI Intelligence', 'Rule Evaluation', 'Inspector Decision'];
  const phaseActiveIndex: Record<AnalysisPhase, number> = { idle: 0, ocr: 1, extraction: 2, rules: 3 };
  const phaseCompleteThrough: Record<AnalysisPhase, number> = { idle: -1, ocr: 0, extraction: 1, rules: 2 };
  
  const activeIndex = analysing ? phaseActiveIndex[analysisPhase] : hasReports ? 4 : hasSuccessfulAnalysis ? 3 : hasImages ? 1 : 0;
  const completeThrough = analysing ? phaseCompleteThrough[analysisPhase] : hasReports ? 4 : hasSuccessfulAnalysis ? 2 : hasImages ? 0 : -1;

  return (
    <div className="space-y-6 sm:space-y-8 max-w-5xl mx-auto pb-12">
      <Link to="/inspections" className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-[var(--text-muted)] hover:text-[var(--brand)] transition-colors">
        <ArrowLeft size={16} /> Back to inspection register
      </Link>
      
      {/* Top Header Card */}
      <section className="depth-1 overflow-hidden relative rounded-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5 p-5 sm:p-7">
          <div className="min-w-0">
            <p className="text-kicker mb-1.5 flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-[var(--brand)]" />
              Inspection <span className="text-[var(--line-strong)] mx-0.5">•</span> {inspection.inspection_number}
            </p>
            <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
              <h2 className="heading-page">{inspection.product_name}</h2>
              <StatusBadge value={inspection.status} />
            </div>
            <p className="mt-2 text-xs sm:text-sm text-[var(--text-muted)] flex flex-wrap items-center gap-2">
              <span className="flex items-center gap-1"><Box size={14} className="text-[var(--text-faint)]" /> {inspection.brand}</span>
              <span className="text-[var(--line-strong)] hidden sm:inline">•</span> 
              <span className="font-mono text-xs text-[var(--text-faint)]">Opened {new Date(inspection.created_at).toLocaleDateString()}</span>
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto shrink-0">
            {hasReports && (
              <div className="flex gap-2 w-full sm:w-auto">
                <button onClick={() => downloadReport(id!, 'pdf')} className="neo-button-secondary flex-1 sm:flex-initial !min-h-[40px] text-xs font-semibold">
                  <FileText size={15} className="text-[var(--danger)]" /> PDF
                </button>
                <button onClick={() => downloadReport(id!, 'docx')} className="neo-button-secondary flex-1 sm:flex-initial !min-h-[40px] text-xs font-semibold">
                  <Download size={15} className="text-[var(--brand)]" /> DOCX
                </button>
              </div>
            )}
            {hasImages && (
              <button 
                onClick={handleAnalyze} 
                disabled={analysing} 
                className="neo-button-primary shadow-md shadow-[var(--brand-soft)] w-full sm:w-auto justify-center !min-h-[40px] text-xs sm:text-sm"
              >
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
        
        <div className="border-t border-[var(--line)] bg-[var(--surface-raised)] px-4 sm:px-8 py-3.5 sm:py-4 overflow-x-auto no-scrollbar">
          <ProgressStages stages={stages} activeIndex={activeIndex} completeThrough={completeThrough} />
        </div>
      </section>

      {error && <Alert tone="error">{error}<button aria-label="Dismiss" className="ml-auto -mr-1 text-current" onClick={() => setError('')}><X size={16} /></button></Alert>}
      {analysisError && <Alert tone="error">{analysisError}<button aria-label="Dismiss" className="ml-auto -mr-1 text-current" onClick={() => setAnalysisError('')}><X size={16} /></button></Alert>}
      {success && <Alert tone="success">{success}</Alert>}
      
      {analysing && <AnalysisProgress phase={analysisPhase} progress={analysisProgress} imageCount={inspection.images.length} processedImageCount={processedImageCount} />}
      
      {/* EXECUTIVE SUMMARY */}
      {hasReports && (
        <section className="depth-2 overflow-hidden bg-[var(--surface)] border border-[var(--line)] rounded-xl">
          <div className="bg-[var(--surface-raised)] px-5 py-3.5 sm:px-6 sm:py-4 border-b border-[var(--line)]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-faint)]">Executive Summary</h3>
          </div>
          <div className="p-4 sm:p-6 space-y-6">
            {complianceReports.map(report => (
              <div key={`exec-${report.inspection_id}`} className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-5">
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center shrink-0 ${report.overall_status === 'PASS' ? 'bg-[var(--success-soft)] text-[var(--success)]' : report.overall_status === 'FAIL' ? 'bg-[var(--danger-soft)] text-[var(--danger)]' : 'bg-[var(--warning-soft)] text-[var(--warning)]'}`}>
                    <ShieldCheck size={30} />
                  </div>
                  <div>
                    <p className="text-xl sm:text-2xl font-bold text-[var(--text)]">{report.overall_status}</p>
                    <p className="text-xs sm:text-sm text-[var(--text-muted)]">Overall Compliance Status</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 sm:gap-3 w-full lg:max-w-2xl">
                  <div className="bg-[var(--surface-raised)] p-2.5 sm:p-3 rounded-lg border border-[var(--line)] text-center">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">Total Checks</p>
                    <p className="text-lg sm:text-xl font-bold text-[var(--text)] mt-0.5">{report.total_rules_checked}</p>
                  </div>
                  <div className="bg-[var(--surface-raised)] p-2.5 sm:p-3 rounded-lg border border-[var(--danger-soft)] text-center">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--danger)]">Failed</p>
                    <p className="text-lg sm:text-xl font-bold text-[var(--danger)] mt-0.5">{report.failed_count}</p>
                  </div>
                  <div className="bg-[var(--surface-raised)] p-2.5 sm:p-3 rounded-lg border border-[var(--warning-soft)] text-center">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--warning)]">Needs Review</p>
                    <p className="text-lg sm:text-xl font-bold text-[var(--warning)] mt-0.5">{report.review_count}</p>
                  </div>
                  <div className="bg-[var(--surface-raised)] p-2.5 sm:p-3 rounded-lg border border-[var(--success-soft)] text-center">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--success)]">Passed</p>
                    <p className="text-lg sm:text-xl font-bold text-[var(--success)] mt-0.5">{report.passed_count}</p>
                  </div>
                  <div className="bg-[var(--surface-raised)] p-2.5 sm:p-3 rounded-lg border border-[var(--line)] text-center col-span-2 sm:col-span-1">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)]">N/A</p>
                    <p className="text-lg sm:text-xl font-bold text-[var(--text-muted)] mt-0.5">{report.not_applicable_count}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* PRODUCT SNAPSHOT */}
      <ProductInfoPanel productInfo={productInfo} />

      {/* ATTENTION REQUIRED */}
      {hasReports && (() => {
        const attentionItems = complianceReports.flatMap(r => r.rule_results.filter(rr => rr.status === 'FAIL' || rr.status === 'REVIEW'));
        if (attentionItems.length === 0) return null;
        return (
          <section className="depth-2 overflow-hidden border-[var(--danger-soft)] border-2 rounded-xl">
            <SectionHeader eyebrow="Action Needed" title="Attention Required" description={`${attentionItems.length} items require immediate attention or manual review.`} />
            <div className="p-3 sm:p-4 grid gap-3 sm:gap-4 bg-[var(--danger-soft)]/10">
               {attentionItems.slice(0, 5).map(item => (
                 <div key={`attn-${item.rule_id}`} className={`bg-[var(--surface)] border p-3.5 sm:p-4 rounded-lg shadow-sm ${item.status === 'FAIL' ? 'border-[var(--danger-soft)]' : 'border-[var(--warning-soft)]'}`}>
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <StatusBadge value={item.status} />
                      <p className="font-bold text-sm sm:text-base text-[var(--text)] flex-1 min-w-0">{item.rule_name}</p>
                    </div>
                    <p className="text-[11px] text-[var(--text-muted)] font-mono mb-2">{item.rule_id}</p>
                    {item.status === 'REVIEW' && item.message && (
                      <p className="text-xs sm:text-sm text-[var(--text)] bg-[var(--warning-soft)]/20 p-2.5 rounded border border-[var(--warning-soft)] mb-2">
                        <span className="font-bold text-[var(--warning)] block text-[10px] uppercase mb-1">Reason</span>
                        {item.message}
                      </p>
                    )}
                    {item.remediation && (
                      <p className="text-xs sm:text-sm text-[var(--text)] bg-[var(--danger-soft)]/10 p-2.5 rounded border border-[var(--danger-soft)]">
                        <span className="font-bold text-[var(--danger)] block text-[10px] uppercase mb-1">Recommendation</span>
                        {item.remediation}
                      </p>
                    )}
                 </div>
               ))}
               {attentionItems.length > 5 && <p className="text-xs sm:text-sm font-bold text-[var(--text-faint)] px-2">+ {attentionItems.length - 5} more items requiring attention</p>}
            </div>
          </section>
        );
      })()}

      {/* GROUPED COMPLIANCE FINDINGS */}
      <ComplianceResultsPanel reports={complianceReports} isAnalyzing={analysing} images={inspection.images.map((image) => ({ id: image.id, url: image.url }))} />

      {/* EVIDENCE UPLOAD SECTION */}
      <section className="depth-2 overflow-hidden flex flex-col rounded-xl">
        <SectionHeader eyebrow="06" title="Evidence" description="Package images establishing the inspection record." />
        <div className="p-4 sm:p-5">
          <div 
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} 
            onDragLeave={() => setDragOver(false)} 
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFileUpload(e.dataTransfer.files); }} 
            className={`border-2 border-dashed rounded-xl p-5 sm:p-6 text-center transition-all duration-200 ${
              dragOver ? 'border-[var(--brand)] bg-[var(--brand-soft)] scale-[1.01]' : 'border-[var(--line-strong)] bg-[var(--surface-raised)] hover:border-[var(--brand)]'
            }`}
          >
            {uploading ? (
              <div>
                <Loader2 size={24} className="mx-auto animate-spin text-[var(--brand)]" />
                <p className="mt-2 text-sm font-semibold text-[var(--text)]">Uploading evidence · {uploadProgress}%</p>
                <div className="mx-auto mt-3 h-1.5 w-44 sm:w-48 overflow-hidden rounded-full bg-[var(--line)]">
                  <div className="h-full bg-[var(--brand)] transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                </div>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => cameraInputRef.current?.click()}
                    className="neo-button-primary !min-h-[42px] text-xs font-semibold sm:hidden"
                  >
                    <Camera size={16} /> Take Photo
                  </button>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="neo-button-secondary !min-h-[42px] text-xs font-semibold sm:hidden"
                  >
                    <Upload size={16} /> Choose File
                  </button>
                </div>

                <div className="hidden sm:flex items-center gap-4 cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                  <div className="w-10 h-10 bg-[var(--surface)] border border-[var(--line-strong)] rounded-full flex items-center justify-center shadow-sm">
                    <Upload size={18} className="text-[var(--brand)]" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-bold text-[var(--text)]">Add package evidence</p>
                    <p className="text-xs text-[var(--text-muted)]">Drop JPG, PNG, or WEBP files here (Max 10 MB)</p>
                  </div>
                </div>

                <p className="text-xs text-[var(--text-muted)] sm:hidden mt-1">
                  Supported formats: JPG, PNG, WEBP (Max 10 MB)
                </p>
              </div>
            )}
            
            {/* Standard file selector */}
            <input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp" multiple className="hidden" onChange={(e) => handleFileUpload(e.target.files)} />
            {/* Mobile camera direct capture */}
            <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={(e) => handleFileUpload(e.target.files)} />
          </div>
        </div>
        
        {hasImages ? (
          <div className="grid gap-3 sm:gap-4 p-4 sm:p-5 pt-0 grid-cols-1 sm:grid-cols-2">
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
          <div className="p-4 sm:p-5 pt-0">
            <EmptyState icon={<ImageIcon size={32} />} title="No evidence attached" description="Upload or capture a package image to begin OCR extraction and compliance analysis." />
          </div>
        )}
      </section>

      {/* TECHNICAL DETAILS */}
      {hasSuccessfulAnalysis && analysisResult && (
        <section className="depth-2 overflow-hidden flex flex-col rounded-xl">
          <SectionHeader eyebrow="07" title="Technical Details" description="Raw OCR extraction and AI analysis results." />
          <div className="p-3.5 sm:p-5 space-y-6">
            {inspection.images.map((image) => {
              const result = analysisResult.images.find(r => r.image_id === image.id);
              if (!result) return null;
              return <OCRResultsPanel key={`ocr-${image.id}`} imageUrl={image.url} result={result} />;
            })}
          </div>
        </section>
      )}

      {hasReports && (
        <section className="depth-2 overflow-hidden flex flex-col items-center justify-center p-6 sm:p-8 bg-[var(--surface-raised)] text-center rounded-xl">
          <div className="w-14 h-14 sm:w-16 sm:h-16 bg-[var(--surface)] border border-[var(--line)] rounded-full flex items-center justify-center mb-3 sm:mb-4">
            <FileText size={24} className="text-[var(--text-faint)]" />
          </div>
          <h3 className="text-base sm:text-lg font-bold text-[var(--text)]">Official report ready</h3>
          <p className="text-xs sm:text-sm text-[var(--text-muted)] mb-5">Download the comprehensive evidence-linked report.</p>
          <div className="flex flex-wrap justify-center gap-3 w-full sm:w-auto">
            <button onClick={() => downloadReport(id!, 'pdf')} className="neo-button-secondary flex-1 sm:flex-initial">
              <FileText size={16} className="text-[var(--danger)]" /> Download PDF
            </button>
            <button onClick={() => downloadReport(id!, 'docx')} className="neo-button-secondary flex-1 sm:flex-initial">
              <Download size={16} className="text-[var(--brand)]" /> Download DOCX
            </button>
          </div>
        </section>
      )}
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
  const steps: Array<{ phase: Exclude<AnalysisPhase, 'idle'>; label: string; shortLabel: string }> = [
    { phase: 'ocr', label: 'OCR & Image Quality', shortLabel: 'OCR' }, 
    { phase: 'extraction', label: 'AI Extraction', shortLabel: 'Extraction' }, 
    { phase: 'rules', label: 'Rule Evaluation', shortLabel: 'Rules' }
  ];
  const order: Record<AnalysisPhase, number> = { idle: 0, ocr: 1, extraction: 2, rules: 3 };
  
  return (
    <section className="depth-2 overflow-hidden border-[var(--brand)] border-2 shadow-lg rounded-xl" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 sm:px-6 py-4 bg-[var(--surface-pale)]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-[var(--surface)] shadow-sm flex items-center justify-center shrink-0">
             <Loader2 size={20} className="animate-spin text-[var(--brand)]" />
          </div>
          <div>
            <p className="text-base sm:text-lg font-bold text-[var(--text)]">{current.title}</p>
            <p className="text-xs sm:text-sm text-[var(--text-muted)] line-clamp-1 sm:line-clamp-none">{current.description}</p>
          </div>
        </div>
        <div className="text-right ml-auto">
          <span className="block font-mono text-lg sm:text-xl font-bold text-[var(--brand)]">{progress}%</span>
          <span className="font-mono text-[10px] sm:text-[11px] font-semibold text-[var(--text-faint)] uppercase tracking-wider">{processedImageCount} / {imageCount} done</span>
        </div>
      </div>
      <div className="h-1.5 bg-[var(--line)]">
        <div className="h-full bg-gradient-to-r from-[var(--brand)] to-[var(--info)] transition-[width] duration-500" style={{ width: `${progress}%` }} />
      </div>
      <div className="px-4 sm:px-6 py-3.5 bg-[var(--surface)]">
         <ol className="flex justify-between items-center text-xs sm:text-sm font-semibold">
           {steps.map((step, idx) => (
             <li key={step.phase} className={`flex items-center gap-1.5 sm:gap-2 flex-1 ${idx !== 0 ? 'justify-center' : ''} ${idx === 2 ? 'justify-end' : ''} ${order[step.phase] < order[phase] ? 'text-[var(--success)]' : step.phase === phase ? 'text-[var(--brand)]' : 'text-[var(--text-faint)]'}`}>
               <span className={`grid h-5 w-5 sm:h-6 sm:w-6 place-items-center rounded-full border-2 text-[10px] shrink-0 ${order[step.phase] < order[phase] ? 'border-[var(--success)] bg-[var(--success-soft)]' : step.phase === phase ? 'border-[var(--brand)] bg-[var(--brand-soft)]' : 'border-[var(--line-strong)]'}`}>
                 {order[step.phase] < order[phase] ? '✓' : order[step.phase]}
               </span>
               <span className="hidden sm:inline">{step.label}</span>
               <span className="sm:hidden text-xs">{step.shortLabel}</span>
             </li>
           ))}
         </ol>
      </div>
    </section>
  );
}

function EvidenceItem({ image, result, pendingDelete, onAskDelete, onCancelDelete, onConfirmDelete }: { image: InspectionImage; result: AnalysisResponse['images'][number] | null; pendingDelete: boolean; onAskDelete: () => void; onCancelDelete: () => void; onConfirmDelete: () => void }) {
  return (
    <section className="depth-2 overflow-hidden h-full flex flex-col rounded-xl">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--line)] px-4 py-3 sm:px-5 sm:py-4 bg-[var(--surface-raised)]">
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs sm:text-sm font-bold text-[var(--text)]" title={image.original_filename}>{image.original_filename}</p>
          <p className="mt-0.5 font-mono text-[10px] uppercase tracking-wider text-[var(--text-faint)]">
            {image.image_type} <span className="mx-1">•</span> {(image.file_size / 1024).toFixed(0)} KB
          </p>
        </div>
        {pendingDelete ? (
          <div className="flex items-center gap-1.5 bg-[var(--danger-soft)] px-2.5 py-1 rounded-lg border border-[var(--danger-soft)]">
            <span className="text-[11px] font-semibold text-[var(--danger)]">Remove?</span>
            <button className="neo-button-danger !min-h-6 !px-2 !py-0.5 !text-[11px] shadow-none" onClick={onConfirmDelete}>Confirm</button>
            <button className="ui-icon-button !w-6 !h-6 bg-[var(--surface)]" onClick={onCancelDelete} aria-label="Cancel"><X size={12} /></button>
          </div>
        ) : (
          <button className="ui-icon-button !w-8 !h-8 bg-[var(--surface)] shadow-sm border border-[var(--line)] hover:!text-[var(--danger)] hover:!border-[var(--danger-soft)]" onClick={onAskDelete} aria-label={`Delete ${image.original_filename}`}>
            <Trash2 size={15} />
          </button>
        )}
      </header>
      <div className="flex-1 flex flex-col">
        {result ? (
          <div className="p-3 sm:p-4 bg-[var(--surface-raised)] border-t border-[var(--line)]">
            <div className="flex justify-between items-center text-xs text-[var(--text-muted)] font-mono mb-2">
              <span>{result.ocr?.blocks?.length || 0} blocks</span>
              <span className="text-[var(--success)] font-semibold">OCR OK</span>
            </div>
            <img src={image.url} alt={image.original_filename} className="w-full h-auto object-contain max-h-[260px] sm:max-h-[300px] rounded border border-[var(--line-strong)]" loading="lazy" />
          </div>
        ) : (
          <div className="p-4 sm:p-5 overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--surface-raised)] flex-1 flex flex-col group relative">
            <img src={image.url} alt={image.original_filename} className="w-full h-auto object-contain flex-1 max-h-[260px] sm:max-h-[300px]" loading="lazy" />
          </div>
        )}
      </div>
    </section>
  );
}
