import React, { useEffect, useRef, useState } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  AlertTriangle,
  Wrench,
  Loader2,
  RotateCcw,
  BarChart3,
  TrendingUp,
  DollarSign,
  Package,
} from 'lucide-react';
import type { ChatMessage, ChatResponse, DatasetProfile } from '../types';
import { api } from '../services/api';
import { InteractiveChart } from './InteractiveChart';
import { DataTablePreview } from './DataTablePreview';

interface ChatInterfaceProps {
  profile: DatasetProfile;
  initialQuery?: string | null;
  onClearInitialQuery?: () => void;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  profile,
  initialQuery,
  onClearInitialQuery,
}) => {
  const initialWelcomeMessage: ChatMessage = {
    id: 'welcome',
    sender: 'assistant',
    text: `Hello! I'm your **AI Data Analyst**. I have loaded and indexed **${profile.filename}** (${profile.row_count.toLocaleString()} rows, ${profile.column_count} columns).\n\nAsk me anything about your revenue, sales trends, top performing products, or regional comparisons. What would you like to explore?`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    followUps: profile.suggested_questions.slice(0, 3),
  };

  const [messages, setMessages] = useState<ChatMessage[]>([initialWelcomeMessage]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (initialQuery) {
      handleSendMessage(initialQuery);
      if (onClearInitialQuery) onClearInitialQuery();
    }
  }, [initialQuery]);

  const handleClearChat = () => {
    setMessages([initialWelcomeMessage]);
  };

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = (queryText || input).trim();
    if (!textToSend || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await api.sendMessage(profile.dataset_id, textToSend);

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: response.message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        dataTable: response.data_table,
        chartSpec: response.chart_spec,
        toolCalls: response.tool_calls,
        followUps: response.follow_up_suggestions,
        limitations: response.limitations,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('Chat request failed:', err);
      const detail = err.response?.data?.detail || err.message || 'Error communicating with analyst agent.';
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        sender: 'assistant',
        text: `**Analysis Error:** ${detail}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        limitations: ['Please verify the relevant columns or try rephrasing your question.'],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatText = (text: string) => {
    return text.split('\n').map((line, lineIdx) => {
      if (line.startsWith('### ')) {
        return (
          <h3 key={lineIdx} className="text-sm font-bold text-slate-900 mt-2 mb-1.5">
            {line.replace('### ', '')}
          </h3>
        );
      }
      if (line.startsWith('- ') || line.startsWith('* ')) {
        const bulletContent = line.slice(2);
        return (
          <li key={lineIdx} className="ml-5 list-disc text-slate-700 my-1">
            <span dangerouslySetInnerHTML={{ __html: parseBold(bulletContent) }} />
          </li>
        );
      }
      if (!line.trim()) {
        return <div key={lineIdx} className="h-2" />;
      }
      return (
        <p key={lineIdx} className="my-1 text-slate-700 leading-relaxed" dangerouslySetInnerHTML={{ __html: parseBold(line) }} />
      );
    });
  };

  const parseBold = (str: string) => {
    return str.replace(/\*\*(.*?)\*\*/g, '<strong class="text-slate-900 font-semibold">$1</strong>');
  };

  return (
    <div className="flex-1 min-w-0 flex flex-col h-full bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden">
      {/* Chat Panel Header */}
      <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between bg-white flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xs sm:text-sm font-bold text-slate-800">
                AI Data Analyst Agent
              </h2>
              <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Ready
              </span>
            </div>
            <p className="text-[11px] text-slate-500 truncate max-w-xs sm:max-w-md">
              Session linked to <span className="font-medium text-slate-700">{profile.filename}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleClearChat}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 border border-slate-200 text-xs font-medium transition-colors"
            title="Reset chat to initial state"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 sm:gap-4 ${
              msg.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {/* Assistant Avatar */}
            {msg.sender === 'assistant' && (
              <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center flex-shrink-0 text-indigo-600 shadow-sm mt-1">
                <Bot className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>
            )}

            {/* Bubble */}
            <div
              className={`max-w-2xl lg:max-w-3xl xl:max-w-4xl rounded-3xl p-5 sm:p-6 ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-md shadow-md shadow-indigo-600/10'
                  : 'bg-slate-50/90 border border-slate-200/80 text-slate-800 rounded-tl-md shadow-sm'
              }`}
            >
              {/* Tool Execution Tags */}
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3.5 pb-2.5 border-b border-slate-200/80">
                  {msg.toolCalls.map((tc, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-white text-indigo-700 border border-indigo-200/80 shadow-2xs"
                      title={tc.result_summary}
                    >
                      <Wrench className="w-3 h-3 text-indigo-500" />
                      {tc.tool_name}
                    </span>
                  ))}
                </div>
              )}

              {/* Message Content */}
              <div className="text-xs sm:text-sm leading-relaxed">
                {msg.sender === 'user' ? (
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                ) : (
                  <div>{formatText(msg.text)}</div>
                )}
              </div>

              {/* Chart */}
              {msg.chartSpec && <InteractiveChart spec={msg.chartSpec} />}

              {/* Table */}
              {msg.dataTable && <DataTablePreview table={msg.dataTable} />}

              {/* Limitations */}
              {msg.limitations && msg.limitations.length > 0 && (
                <div className="mt-4 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600" />
                  <div className="space-y-0.5">
                    {msg.limitations.map((lim, i) => (
                      <p key={i}>{lim}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Follow-up Questions */}
              {msg.followUps && msg.followUps.length > 0 && (
                <div className="mt-4 pt-3.5 border-t border-slate-200/80">
                  <span className="text-[11px] uppercase font-bold text-slate-500 block mb-2 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                    Suggested Next Questions:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {msg.followUps.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSendMessage(q)}
                        className="text-left text-xs px-3 py-1.5 rounded-xl bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-indigo-700 font-medium transition-colors shadow-2xs"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Timestamp */}
              <div
                className={`text-[10px] mt-2.5 font-mono text-right ${
                  msg.sender === 'user' ? 'text-indigo-200' : 'text-slate-400'
                }`}
              >
                {msg.timestamp}
              </div>
            </div>

            {/* User Avatar */}
            {msg.sender === 'user' && (
              <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-2xl bg-slate-200 border border-slate-300 flex items-center justify-center flex-shrink-0 mt-1 text-slate-600">
                <User className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>
            )}
          </div>
        ))}

        {/* Quick Starter Cards (When only initial message exists) */}
        {messages.length === 1 && (
          <div className="mt-6 pt-4 border-t border-slate-100">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider block mb-3 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              Popular Questions to Get Started:
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <button
                onClick={() => handleSendMessage('What is the total revenue, average order value, and total units sold?')}
                className="p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/70 border border-slate-200 hover:border-indigo-200 text-left transition-all group flex items-start gap-3 shadow-2xs"
              >
                <div className="w-8 h-8 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 flex-shrink-0 mt-0.5">
                  <DollarSign className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-800 group-hover:text-indigo-700">
                    Total Revenue & Key Metrics
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    What is the total revenue, average order value, and units sold?
                  </div>
                </div>
              </button>

              <button
                onClick={() => handleSendMessage('Which product generated the highest sales? Show top 5 products.')}
                className="p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/70 border border-slate-200 hover:border-indigo-200 text-left transition-all group flex items-start gap-3 shadow-2xs"
              >
                <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0 mt-0.5">
                  <Package className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-800 group-hover:text-indigo-700">
                    Top Selling Products
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Which products generated highest sales? Show top 5.
                  </div>
                </div>
              </button>

              <button
                onClick={() => handleSendMessage('Plot monthly revenue as a line chart')}
                className="p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/70 border border-slate-200 hover:border-indigo-200 text-left transition-all group flex items-start gap-3 shadow-2xs"
              >
                <div className="w-8 h-8 rounded-xl bg-cyan-50 border border-cyan-100 flex items-center justify-center text-cyan-600 flex-shrink-0 mt-0.5">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-800 group-hover:text-indigo-700">
                    Monthly Revenue Trend
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Plot monthly sales trends over time as a line chart.
                  </div>
                </div>
              </button>

              <button
                onClick={() => handleSendMessage('Create a bar chart showing revenue by category')}
                className="p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/70 border border-slate-200 hover:border-indigo-200 text-left transition-all group flex items-start gap-3 shadow-2xs"
              >
                <div className="w-8 h-8 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 flex-shrink-0 mt-0.5">
                  <BarChart3 className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-800 group-hover:text-indigo-700">
                    Category Breakdown
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Create a bar chart showing revenue distribution across categories.
                  </div>
                </div>
              </button>
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-start gap-4">
            <div className="w-9 h-9 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center flex-shrink-0 text-indigo-600 animate-pulse">
              <Bot className="w-5 h-5" />
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-3xl rounded-tl-md p-4 sm:p-5 flex items-center gap-3 shadow-sm">
              <Loader2 className="w-4 h-4 text-indigo-600 animate-spin" />
              <span className="text-xs sm:text-sm text-slate-600 font-medium">
                Analyst reasoning, selecting deterministic tools & calculating metrics...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 sm:p-5 border-t border-slate-200 bg-white flex-shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-end gap-3"
        >
          <div className="flex-1 relative">
            <textarea
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your data... (e.g. 'What is the total revenue?', 'Show top 5 products', 'Create a bar chart')"
              className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none transition-all shadow-inner"
              disabled={isLoading}
            />
            <div className="text-[10px] text-slate-400 mt-1 pl-1 flex items-center justify-between">
              <span>Press <strong>Enter ↵</strong> to send • <strong>Shift + Enter</strong> for new line</span>
              <span className="hidden sm:inline">Deterministic Python Pandas Engine</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3.5 mb-5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white transition-all shadow-md shadow-indigo-600/20 flex-shrink-0"
            title="Send query"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
