import React from 'react';
import { BarChart3, Sparkles, RefreshCw, Layers, MessageSquare, Database, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import type { DatasetProfile } from '../types';

interface NavbarProps {
  profile: DatasetProfile | null;
  llmConfigured: boolean;
  onReset: () => void;
  onOpenPreview: () => void;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
  activeTab?: 'chat' | 'dataset';
  onTabChange?: (tab: 'chat' | 'dataset') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  profile,
  llmConfigured,
  onReset,
  onOpenPreview,
  isSidebarOpen = true,
  onToggleSidebar,
  activeTab = 'chat',
  onTabChange,
}) => {
  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-30 px-4 sm:px-6 lg:px-8 py-3 shadow-xs">
      <div className="w-full flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3.5 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-3">
            {profile && onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                className="hidden lg:flex p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 border border-slate-200 transition-colors"
                title={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
              >
                {isSidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4 text-indigo-600" />}
              </button>
            )}

            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center shadow-md shadow-indigo-500/20 flex-shrink-0">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
                  AI E-Commerce Data Analyst
                </h1>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                  v1.0
                </span>
              </div>
              <p className="hidden sm:block text-[11px] text-slate-500">
                Conversational Business Intelligence & Deterministic Pandas Analytics
              </p>
            </div>
          </div>

          {/* Mobile Tab Selector */}
          {profile && onTabChange && (
            <div className="flex lg:hidden items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
              <button
                onClick={() => onTabChange('chat')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-all ${
                  activeTab === 'chat'
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Chat</span>
              </button>
              <button
                onClick={() => onTabChange('dataset')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-all ${
                  activeTab === 'dataset'
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                <span>Dataset</span>
              </button>
            </div>
          )}
        </div>

        {/* Right Info & Actions */}
        <div className="flex items-center gap-2.5 flex-wrap w-full md:w-auto justify-end">
          {/* LLM Status Badge */}
          <div
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${
              llmConfigured
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-amber-50 border-amber-200 text-amber-700'
            }`}
            title={
              llmConfigured
                ? 'OpenAI-compatible LLM connected'
                : 'Offline Deterministic Python Analytics Engine active. Configure LLM_API_KEY in backend/.env for generative chat.'
            }
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{llmConfigured ? 'LLM Agent Active' : 'Deterministic Mode'}</span>
          </div>

          {/* Active Dataset Status */}
          {profile && (
            <div className="flex items-center gap-2">
              <button
                onClick={onOpenPreview}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 border border-slate-200 text-slate-700 text-xs font-medium transition-colors shadow-2xs"
                title="Inspect dataset preview table"
              >
                <Layers className="w-3.5 h-3.5 text-indigo-600" />
                <span className="truncate max-w-[130px] font-medium">{profile.filename}</span>
                <span className="text-[10px] font-mono text-slate-600 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                  {profile.row_count.toLocaleString()} rows
                </span>
              </button>

              <button
                onClick={onReset}
                className="p-2 rounded-xl bg-slate-100 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 border border-slate-200 text-slate-500 transition-colors shadow-2xs"
                title="Switch dataset / reset session"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
