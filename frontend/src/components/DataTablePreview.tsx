import React from 'react';
import type { DataTable } from '../types';

interface DataTablePreviewProps {
  table: DataTable;
}

export const DataTablePreview: React.FC<DataTablePreviewProps> = ({ table }) => {
  const { title, columns, rows, total_count } = table;

  return (
    <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden my-4 shadow-sm">
      {title && (
        <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-800">{title}</span>
          <span className="text-[11px] text-slate-500 font-medium">
            Showing {rows.length} of {total_count} records
          </span>
        </div>
      )}
      <div className="overflow-x-auto max-h-72">
        <table className="w-full text-left text-xs text-slate-700">
          <thead className="bg-slate-100/80 text-[11px] text-slate-600 uppercase tracking-wider sticky top-0 border-b border-slate-200">
            <tr>
              {columns.map((col) => (
                <th key={col} className="px-4 py-3 font-semibold whitespace-nowrap">
                  {col.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-indigo-50/30 transition-colors">
                {columns.map((col) => {
                  const val = row[col];
                  const isNum = typeof val === 'number';
                  return (
                    <td
                      key={col}
                      className={`px-4 py-2.5 whitespace-nowrap font-mono text-[11px] ${
                        isNum ? 'text-indigo-600 font-semibold' : 'text-slate-800'
                      }`}
                    >
                      {val !== null && val !== undefined
                        ? isNum
                          ? val.toLocaleString(undefined, { maximumFractionDigits: 2 })
                          : String(val)
                        : '-'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
