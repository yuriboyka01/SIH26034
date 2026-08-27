/**
 * Inspection detail page — Phase 2: upload images + trigger OCR analysis.
 * Shows bounding-box overlay and detected text blocks after analysis.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  getInspection,
  uploadInspectionImage,
  deleteInspectionImage,
  type Inspection,
} from '../api/inspections';
import { analyzeInspection, getAnalysisResults, type AnalysisResponse } from '../api/analysis';
import OCRResultsPanel from '../components/OCRResultsPanel';
import {
  ArrowLeft,
  Upload,
  Trash2,
  ImageIcon,
  Loader2,
  AlertCircle,
  CheckCircle,
  X,
  ScanText,
  RefreshCw,
} from 'lucide-react';

export default function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Phase 2: Analysis state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysing, setAnalysing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');

  const fetchInspection = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getInspection(id);
      setInspection(data);
    } catch (err) {
      console.error('Failed to fetch inspection:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  // On mount: load inspection + any persisted OCR results
  useEffect(() => {
    fetchInspection();
    if (id) {
      getAnalysisResults(id)
        .then((res) => {
          // Only show if at least one image has been analysed
          const hasResults = res.images.some((img) => img.status === 'OK');
          if (hasResults) setAnalysisResult(res);
        })
        .catch(() => {
          // No results yet — that's fine
        });
    }
  }, [fetchInspection, id]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !id) return;

    setError('');
    setSuccessMsg('');
    setUploading(true);
    setUploadProgress(0);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!validTypes.includes(file.type)) {
          setError(`${file.name}: Only JPG, PNG, and WEBP images are supported.`);
          continue;
        }

        if (file.size > 10 * 1024 * 1024) {
          setError(`${file.name}: File size exceeds 10MB limit.`);
          continue;
        }

        await uploadInspectionImage(id, file, 'OTHER', (progress) => {
          setUploadProgress(progress);
        });
      }

      setSuccessMsg('Image(s) uploaded successfully!');
      setTimeout(() => setSuccessMsg(''), 3000);
      await fetchInspection();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } } };
      setError(e?.response?.data?.error?.message || 'Failed to upload image.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (imageId: string) => {
    if (!id || !confirm('Delete this image?')) return;

    try {
      await deleteInspectionImage(id, imageId);
      await fetchInspection();
      setSuccessMsg('Image deleted.');
      setTimeout(() => setSuccessMsg(''), 2000);
      // Clear analysis if images changed
      setAnalysisResult(null);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } } };
      setError(e?.response?.data?.error?.message || 'Failed to delete image.');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const handleAnalyze = async () => {
    if (!id) return;
    setAnalysisError('');
    setAnalysing(true);
    try {
      const result = await analyzeInspection(id);
      setAnalysisResult(result);
      // Refresh inspection to get updated status
      await fetchInspection();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } } };
      setAnalysisError(e?.response?.data?.error?.message || 'Analysis failed. Please try again.');
    } finally {
      setAnalysing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
      </div>
    );
  }

  if (!inspection) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Inspection not found.</p>
        <Link to="/inspections" className="text-indigo-400 hover:text-indigo-300 text-sm mt-2 inline-block">
          Back to Inspections
        </Link>
      </div>
    );
  }

  const statusStyles: Record<string, string> = {
    CREATED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    IMAGES_UPLOADED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    PROCESSING: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    COMPLETED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    NEEDS_REVIEW: 'bg-red-500/10 text-red-400 border-red-500/20',
  };

  const statusLabels: Record<string, string> = {
    CREATED: 'Created',
    IMAGES_UPLOADED: 'Images Uploaded',
    PROCESSING: 'Processing',
    COMPLETED: 'Completed',
    NEEDS_REVIEW: 'Needs Review',
  };

  // Map image id → url for OCR overlay (reserved for future use)
  // const imageUrlMap = Object.fromEntries(inspection.images.map((img) => [img.id, img.url]));

  const hasImages = inspection.images.length > 0;

  return (
    <div className="animate-fade-in">
      {/* Back link */}
      <Link
        to="/inspections"
        className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Inspections
      </Link>

      {/* Inspection Header */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-xl font-bold text-white">{inspection.product_name}</h1>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                  statusStyles[inspection.status] || statusStyles['CREATED']
                }`}
              >
                {statusLabels[inspection.status] || inspection.status}
              </span>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-slate-400">
                <span className="text-slate-500">Brand:</span>{' '}
                <span className="text-slate-200">{inspection.brand}</span>
              </p>
              <p className="text-sm text-slate-400">
                <span className="text-slate-500">Inspection #:</span>{' '}
                <span className="font-mono text-slate-200">{inspection.inspection_number}</span>
              </p>
              <p className="text-sm text-slate-400">
                <span className="text-slate-500">Created:</span>{' '}
                {new Date(inspection.created_at).toLocaleString()}
              </p>
            </div>
          </div>

          {/* ── Analyze Button ── */}
          {hasImages && (
            <button
              onClick={handleAnalyze}
              disabled={analysing}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-60"
              style={{
                background: analysing
                  ? 'rgba(99,102,241,0.3)'
                  : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff',
                boxShadow: analysing ? 'none' : '0 4px 20px rgba(99,102,241,0.4)',
              }}
            >
              {analysing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analysing…
                </>
              ) : analysisResult ? (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Re-Analyse
                </>
              ) : (
                <>
                  <ScanText className="w-4 h-4" />
                  Analyse Inspection
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="flex items-center justify-between bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
          <button onClick={() => setError('')}>
            <X className="w-4 h-4 text-red-400 hover:text-red-300" />
          </button>
        </div>
      )}

      {analysisError && (
        <div className="flex items-center justify-between bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-400">{analysisError}</p>
          </div>
          <button onClick={() => setAnalysisError('')}>
            <X className="w-4 h-4 text-red-400 hover:text-red-300" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 mb-4">
          <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <p className="text-sm text-emerald-400">{successMsg}</p>
        </div>
      )}

      {/* Analysing indicator */}
      {analysing && (
        <div className="flex items-center gap-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4 mb-6">
          <Loader2 className="w-5 h-5 text-indigo-400 animate-spin flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-indigo-300">Running OCR analysis…</p>
            <p className="text-xs text-slate-400 mt-0.5">
              OpenCV preprocessing + PaddleOCR · This may take 10–30 seconds per image
            </p>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white mb-3">Upload Images</h2>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer ${
            dragOver
              ? 'border-indigo-400 bg-indigo-500/10'
              : 'border-slate-600 hover:border-slate-500 bg-slate-800/30'
          }`}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploading ? (
            <div className="space-y-3">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
              <p className="text-sm text-slate-300">Uploading… {uploadProgress}%</p>
              <div className="w-48 mx-auto bg-slate-700 rounded-full h-1.5">
                <div
                  className="bg-indigo-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : (
            <>
              <Upload className="w-8 h-8 text-slate-400 mx-auto mb-3" />
              <p className="text-sm text-slate-300 mb-1">
                Drag &amp; drop images here, or click to browse
              </p>
              <p className="text-xs text-slate-500">
                Supports JPG, PNG, WEBP · Max 10MB per file
              </p>
            </>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.webp"
            multiple
            className="hidden"
            onChange={(e) => handleFileUpload(e.target.files)}
          />
        </div>
      </div>

      {/* ── Images + OCR Results ── */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">
          Uploaded Images ({inspection.images.length})
        </h2>

        {inspection.images.length === 0 ? (
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-8 text-center">
            <ImageIcon className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No images uploaded yet</p>
            <p className="text-slate-500 text-xs mt-1">
              Upload package images to begin the inspection
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {inspection.images.map((image) => {
              // Find OCR result for this image
              const ocrResult = analysisResult?.images.find(
                (r) => r.image_id === image.id
              ) ?? null;

              return (
                <div
                  key={image.id}
                  className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden"
                >
                  {/* Image header row */}
                  <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
                    <div className="flex items-center gap-2">
                      <ImageIcon className="w-4 h-4 text-slate-400" />
                      <span className="text-sm text-slate-300 truncate max-w-xs">
                        {image.original_filename}
                      </span>
                      <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">
                        {image.image_type}
                      </span>
                      <span className="text-xs text-slate-500">
                        {(image.file_size / 1024).toFixed(0)} KB
                      </span>
                    </div>
                    <button
                      onClick={() => handleDelete(image.id)}
                      className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                      title="Delete image"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Content: Image + OCR panel */}
                  <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Raw image thumbnail */}
                    <div>
                      <img
                        src={image.url}
                        alt={image.original_filename}
                        className="w-full rounded-xl object-contain max-h-96"
                        loading="lazy"
                      />
                    </div>

                    {/* OCR Results */}
                    <div>
                      {ocrResult ? (
                        <OCRResultsPanel imageUrl={image.url} result={ocrResult} />
                      ) : (
                        <div
                          className="h-full flex flex-col items-center justify-center rounded-xl p-6 text-center"
                          style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.07)',
                            minHeight: '200px',
                          }}
                        >
                          <ScanText className="w-10 h-10 mb-3" style={{ color: 'rgba(255,255,255,0.2)' }} />
                          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.4)' }}>
                            Click <strong className="text-indigo-400">Analyse Inspection</strong> to run OCR
                          </p>
                          <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.25)' }}>
                            Bounding boxes and detected text will appear here
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
