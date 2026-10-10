import React, { useState } from 'react';
import { X, Check, AlertCircle, Save } from 'lucide-react';
import type { DatasetProfile } from '../types';
import { api } from '../services/api';

interface SchemaMappingModalProps {
  profile: DatasetProfile;
  isOpen: boolean;
  onClose: () => void;
  onMappingsUpdated: (updatedProfile: DatasetProfile) => void;
}

const COMMON_ROLES = [
  { role: 'revenue', label: 'Revenue / Sales Amount', desc: 'Total sales value of the line item or transaction' },
  { role: 'category', label: 'Product Category', desc: 'Department or category grouping' },
  { role: 'product', label: 'Product Name / ID', desc: 'Unique item name or SKU' },
  { role: 'order_date', label: 'Order Date', desc: 'Transaction timestamp for timeline trends' },
  { role: 'region', label: 'Region / Location', desc: 'Geographic market, territory, or city' },
  { role: 'quantity', label: 'Quantity Sold', desc: 'Units purchased' },
  { role: 'unit_price', label: 'Unit Price', desc: 'Price per individual unit' },
  { role: 'order_id', label: 'Order ID', desc: 'Unique transaction ID (used for order count)' },
  { role: 'discount', label: 'Discount', desc: 'Percentage or dollar discount' },
];

export const SchemaMappingModal: React.FC<SchemaMappingModalProps> = ({
  profile,
  isOpen,
  onClose,
  onMappingsUpdated,
}) => {
  if (!isOpen) return null;

  const currentMappings = Object.entries(profile.semantic_mappings).reduce((acc, [k, v]) => {
    acc[k] = v.column_name;
    return acc;
  }, {} as Record<string, string>);

  const [mappings, setMappings] = useState<Record<string, string>>(currentMappings);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availableColumns = profile.columns.map((c) => c.name);

  const handleSelectChange = (role: string, colName: string) => {
    setMappings((prev) => ({
      ...prev,
      [role]: colName,
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await api.updateMappings(profile.dataset_id, mappings);
      const updated = await api.getProfile(profile.dataset_id);
      onMappingsUpdated(updated);
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        onClose();
      }, 1000);
    } catch (err: any) {
      console.error('Failed to update mappings:', err);
      setError(err.response?.data?.detail || 'Failed to save mappings.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div>
            <h3 className="text-base font-bold text-slate-900">Semantic Column Mapping</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Confirm or assign business roles to columns in <span className="font-mono text-indigo-600 font-medium">{profile.filename}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-slate-200/60 text-slate-400 hover:text-slate-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-3.5 flex-1">
          {error && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-3">
            {COMMON_ROLES.map(({ role, label, desc }) => {
              const selectedCol = mappings[role] || '';
              return (
                <div
                  key={role}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-2xl bg-slate-50/80 border border-slate-200/80 gap-3"
                >
                  <div className="flex-1">
                    <span className="text-xs font-bold text-slate-800 block">{label}</span>
                    <span className="text-[11px] text-slate-500 block">{desc}</span>
                  </div>

                  <div className="sm:w-56">
                    <select
                      value={selectedCol}
                      onChange={(e) => handleSelectChange(role, e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono shadow-2xs"
                    >
                      <option value="">-- None / Unmapped --</option>
                      {availableColumns.map((col) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/60 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-200/60 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50"
          >
            {saveSuccess ? (
              <>
                <Check className="w-4 h-4 text-white" />
                <span>Saved!</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>{isSaving ? 'Saving...' : 'Apply Mappings'}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
