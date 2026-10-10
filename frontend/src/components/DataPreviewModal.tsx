import React, { useEffect, useState } from 'react';
import { X, Layers, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import type { DatasetPreview } from '../types';

interface DataPreviewModalProps {
  datasetId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const DataPreviewModal: React.FC<DataPreviewModalProps> = ({
  datasetId,
  isOpen,
  onClose,
}) => {
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && datasetId) {
      setLoading(true);
      api.getPreview(datasetId, 25)
        .then((data) => setPreview(data))
        .catch((err) => console.error('Failed to load preview:', err))
        .finally(() => setLoading(false));
    }
  }, [isOpen, datasetId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Dataset Preview Table</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {preview ? `${preview.filename} • Showing first ${preview.preview_rows.length} of ${preview.total_rows.toLocaleString()} records` : 'Loading records...'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-slate-200/60 text-slate-400 hover:text-slate-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-3" />
              <span className="text-xs font-medium">Fetching preview rows...</span>
            </div>
          ) : preview && preview.preview_rows.length > 0 ? (
            <div className="border border-slate-200 rounded-2xl overflow-hidden shadow-2xs">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-100/80 text-[11px] text-slate-600 uppercase tracking-wider sticky top-0 border-b border-slate-200">
                  <tr>
                    {preview.columns.map((col) => (
                      <th key={col} className="px-4 py-3 font-semibold whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {preview.preview_rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                      {preview.columns.map((col) => (
                        <td key={col} className="px-4 py-2.5 whitespace-nowrap font-mono text-[11px]">
                          {row[col] !== null && row[col] !== undefined ? String(row[col]) : (
                            <span className="text-slate-400 italic font-sans">null</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400 text-xs">
              No preview data available for this dataset.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/60 text-right">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-xs font-semibold bg-slate-200 hover:bg-slate-300/80 text-slate-700 transition-colors shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
