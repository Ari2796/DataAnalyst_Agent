import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { ChartSpec } from '../types';

interface InteractiveChartProps {
  spec: ChartSpec;
}

const LIGHT_PALETTE = [
  '#4f46e5', // Indigo 600
  '#059669', // Emerald 600
  '#d97706', // Amber 600
  '#db2777', // Pink 600
  '#7c3aed', // Violet 600
  '#0284c7', // Sky 600
  '#ea580c', // Orange 600
  '#0d9488', // Teal 600
];

export const InteractiveChart: React.FC<InteractiveChartProps> = ({ spec }) => {
  const { chart_type, title, description, x_axis_key, series, data, x_axis_label, y_axis_label } = spec;

  const tooltipStyle = {
    backgroundColor: '#ffffff',
    borderColor: '#e2e8f0',
    borderRadius: '12px',
    color: '#0f172a',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04)',
    padding: '10px 14px',
    fontSize: '12px',
  };

  const renderChart = () => {
    switch (chart_type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={340}>
            <LineChart data={data} margin={{ top: 15, right: 30, left: 15, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey={x_axis_key}
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={{ stroke: '#cbd5e1' }}
                label={{ value: x_axis_label || x_axis_key, position: 'insideBottom', offset: -15, fill: '#64748b', fontSize: 11 }}
              />
              <YAxis
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={{ stroke: '#cbd5e1' }}
                label={{ value: y_axis_label || 'Value', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ paddingTop: '12px', fontSize: '12px' }} />
              {series.map((s, idx) => (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.name || s.key}
                  stroke={s.color || LIGHT_PALETTE[idx % LIGHT_PALETTE.length]}
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: s.color || LIGHT_PALETTE[idx % LIGHT_PALETTE.length], stroke: '#ffffff', strokeWidth: 2 }}
                  activeDot={{ r: 7 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie': {
        const valueKey = series[0]?.key || Object.keys(data[0] || {}).find(k => k !== x_axis_key) || 'value';
        return (
          <ResponsiveContainer width="100%" height={340}>
            <PieChart>
              <Pie
                data={data}
                dataKey={valueKey}
                nameKey={x_axis_key}
                cx="50%"
                cy="50%"
                outerRadius={115}
                innerRadius={48}
                paddingAngle={4}
                label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ''}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={LIGHT_PALETTE[index % LIGHT_PALETTE.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        );
      }

      case 'scatter': {
        const yKey = series[0]?.key || Object.keys(data[0] || {}).find(k => k !== x_axis_key) || 'y';
        return (
          <ResponsiveContainer width="100%" height={340}>
            <ScatterChart margin={{ top: 15, right: 30, left: 15, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey={x_axis_key}
                type="number"
                name={x_axis_label || x_axis_key}
                stroke="#64748b"
                fontSize={12}
                label={{ value: x_axis_label || x_axis_key, position: 'insideBottom', offset: -15, fill: '#64748b', fontSize: 11 }}
              />
              <YAxis
                dataKey={yKey}
                type="number"
                name={y_axis_label || yKey}
                stroke="#64748b"
                fontSize={12}
                label={{ value: y_axis_label || yKey, angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
              />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={tooltipStyle} />
              <Scatter name={`${y_axis_label || yKey} vs ${x_axis_label || x_axis_key}`} data={data} fill="#4f46e5" />
            </ScatterChart>
          </ResponsiveContainer>
        );
      }

      case 'bar':
      default:
        return (
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={data} margin={{ top: 15, right: 30, left: 15, bottom: 35 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey={x_axis_key}
                stroke="#64748b"
                fontSize={11}
                angle={-20}
                textAnchor="end"
                interval={0}
                tickLine={false}
                axisLine={{ stroke: '#cbd5e1' }}
              />
              <YAxis
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={{ stroke: '#cbd5e1' }}
                label={{ value: y_axis_label || 'Value', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
              />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#f1f5f9' }} />
              <Legend wrapperStyle={{ paddingTop: '12px', fontSize: '12px' }} />
              {series.map((s, idx) => (
                <Bar
                  key={s.key}
                  dataKey={s.key}
                  name={s.name || s.key}
                  fill={s.color || LIGHT_PALETTE[idx % LIGHT_PALETTE.length]}
                  radius={[6, 6, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm my-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
            {title}
          </h4>
          {description && (
            <p className="text-xs text-slate-500 mt-1">{description}</p>
          )}
        </div>
        <span className="text-[11px] font-semibold uppercase bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-md border border-indigo-200">
          {chart_type} chart
        </span>
      </div>
      <div className="w-full overflow-hidden">{renderChart()}</div>
    </div>
  );
};
