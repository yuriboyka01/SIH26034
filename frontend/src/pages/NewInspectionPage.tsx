/**
 * New Inspection page — form to create a new inspection.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createInspection } from '../api/inspections';
import { Package, Tag, Loader2, AlertCircle } from 'lucide-react';

export default function NewInspectionPage() {
  const [productName, setProductName] = useState('');
  const [brand, setBrand] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const inspection = await createInspection({
        product_name: productName,
        brand,
      });
      navigate(`/inspections/${inspection.id}`);
    } catch (err: any) {
      const msg =
        err?.response?.data?.error?.message || 'Failed to create inspection.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in max-w-lg">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">New Inspection</h1>
        <p className="text-sm text-slate-400 mt-1">
          Create a new package compliance inspection
        </p>
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
        {error && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="productName"
              className="block text-sm font-medium text-slate-300 mb-1.5"
            >
              Product Name
            </label>
            <div className="relative">
              <Package className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                id="productName"
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                required
                placeholder="e.g., Basmati Rice 5kg"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="brand"
              className="block text-sm font-medium text-slate-300 mb-1.5"
            >
              Brand
            </label>
            <div className="relative">
              <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                id="brand"
                type="text"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                required
                placeholder="e.g., India Gate"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white font-medium rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/25"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Inspection'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
