import React, { useState } from 'react';
import {
  Database,
  Layers,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Settings2,
  Calendar,
  DollarSign,
  Tag,
  Package,
  Workflow,
} from 'lucide-react';
import type { DatasetProfile } from '../types';

interface DatasetSidebarProps {
  profile: DatasetProfile;
  onSelectQuery?: (query: string) => void;
  onOpenMappingsModal: () => void;
  onOpenPreview: () => void;
}

export const DatasetSidebar: React.FC<DatasetSidebarProps> = ({
  profile,
  onOpenMappingsModal,
  onOpenPreview,
}) => {
  const [showColumnsList, setShowColumnsList] = useState(false);

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'revenue':
      case 'unit_price':
      case 'profit':
        return <DollarSign className="w-3.5 h-3.5 text-emerald-600" />;
      case 'order_date':
        return <Calendar className="w-3.5 h-3.5 text-cyan-600" />;
      case 'category':
        return <Tag className="w-3.5 h-3.5 text-amber-600" />;
      case 'product':
        return <Package className="w-3.5 h-3.5 text-indigo-600" />;
      default:
        return <Layers className="w-3.5 h-3.5 text-slate-500" />;
    }
  };

  return (
    <aside className="w-full lg:w-80 xl:w-96 flex-shrink-0 flex flex-col h-full bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden">
      {/* Sidebar Header */}
      <div className="p-5 pb-3 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-indigo-600" />
          <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Dataset Details
          </h2>
        </div>
        <button
          onClick={onOpenPreview}
          className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold hover:underline"
        >
          Preview Table
        </button>
      </div>

      {/* Scrollable Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Dataset Summary */}
        <div>
          <div className="text-xs font-semibold text-slate-900 truncate mb-3" title={profile.filename}>
            {profile.filename}
          </div>

          {/* Metric Tiles */}
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="bg-slate-50 p-2.5 rounded-2xl border border-slate-100">
              <span className="text-[10px] text-slate-500 block mb-0.5">Rows</span>
              <span className="text-xs font-bold text-indigo-600 font-mono">
                {profile.row_count.toLocaleString()}
              </span>
            </div>
            <div className="bg-slate-50 p-2.5 rounded-2xl border border-slate-100">
              <span className="text-[10px] text-slate-500 block mb-0.5">Cols</span>
              <span className="text-xs font-bold text-slate-800 font-mono">
                {profile.column_count}
              </span>
            </div>
            <div className="bg-slate-50 p-2.5 rounded-2xl border border-slate-100">
              <span className="text-[10px] text-slate-500 block mb-0.5">Dupes</span>
              <span className="text-xs font-bold text-slate-800 font-mono">
                {profile.duplicate_rows}
              </span>
            </div>
          </div>
        </div>

        {/* Semantic Mappings Snapshot */}
        <div className="pt-2 border-t border-slate-100">
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Business Roles
            </span>
            <button
              onClick={onOpenMappingsModal}
              className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1 hover:underline"
            >
              <Settings2 className="w-3 h-3" />
              Edit
            </button>
          </div>

          <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
            {Object.entries(profile.semantic_mappings).map(([role, map]) => (
              <div
                key={role}
                className="flex items-center justify-between text-xs py-1.5 px-3 rounded-xl bg-slate-50 border border-slate-100"
              >
                <div className="flex items-center gap-2 text-slate-700 capitalize text-xs">
                  {getRoleIcon(role)}
                  <span className="font-medium text-[11px]">{role.replace('_', ' ')}</span>
                </div>
                <span className="font-mono text-[10px] text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100 truncate max-w-[120px]">
                  {map.column_name}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Expandable All Columns */}
        <div className="pt-2 border-t border-slate-100">
          <button
            onClick={() => setShowColumnsList(!showColumnsList)}
            className="w-full flex items-center justify-between text-xs text-slate-600 hover:text-slate-900 font-medium transition-colors py-1"
          >
            <span>All Columns ({profile.columns.length})</span>
            {showColumnsList ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showColumnsList && (
            <div className="mt-2 space-y-1.5 max-h-44 overflow-y-auto pr-1">
              {profile.columns.map((col) => (
                <div
                  key={col.name}
                  className="p-2 rounded-xl bg-slate-50 border border-slate-100 text-xs flex items-center justify-between"
                >
                  <span className="font-mono text-slate-700 font-medium truncate max-w-[130px]" title={col.name}>
                    {col.name}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-white border border-slate-200 text-slate-600 font-mono">
                      {col.general_type}
                    </span>
                    {col.missing_count > 0 && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200">
                        {col.missing_percentage}% null
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Simple Flow of the Agent Project */}
        <div className="pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2 mb-3">
            <Workflow className="w-3.5 h-3.5 text-indigo-600" />
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Agent Workflow
            </h3>
          </div>

          <div className="relative pl-3 space-y-2.5 before:absolute before:left-[17px] before:top-2 before:bottom-2 before:w-0.5 before:bg-indigo-100">
            {/* Step 1 */}
            <div className="relative flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 flex-shrink-0 z-10 text-[10px] font-bold">
                1
              </div>
              <div className="flex-1 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800">CSV Profiling</span>
                  <span className="text-[9px] font-mono font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">Done</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Parses schema & stats distributions
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-full bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 flex-shrink-0 z-10 text-[10px] font-bold">
                2
              </div>
              <div className="flex-1 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800">Role Mapping</span>
                  <span className="text-[9px] font-mono font-medium text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">Mapped</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Detects revenue, date, product & roles
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-full bg-cyan-50 border border-cyan-200 flex items-center justify-center text-cyan-600 flex-shrink-0 z-10 text-[10px] font-bold">
                3
              </div>
              <div className="flex-1 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800">User Query</span>
                  <span className="text-[9px] font-mono font-medium text-cyan-700 bg-cyan-50 px-1.5 py-0.5 rounded border border-cyan-200">Active</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Natural language question or chart request
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="relative flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 flex-shrink-0 z-10 text-[10px] font-bold">
                4
              </div>
              <div className="flex-1 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800">Pandas Engine</span>
                  <span className="text-[9px] font-mono font-medium text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">Verified</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Deterministic Python tools (no math hallucinations)
                </p>
              </div>
            </div>

            {/* Step 5 */}
            <div className="relative flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-full bg-violet-50 border border-violet-200 flex items-center justify-center text-violet-600 flex-shrink-0 z-10 text-[10px] font-bold">
                5
              </div>
              <div className="flex-1 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800">Insights & Charts</span>
                  <span className="text-[9px] font-mono font-medium text-violet-700 bg-violet-50 px-1.5 py-0.5 rounded border border-violet-200">Output</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Interactive Recharts + executive summaries
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
