import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid,
  ErrorBar,
} from 'recharts';

interface ErrorBarChartProps {
  seriesA: string;
  seriesB: string;
  valueA?: number;
  valueB?: number;
  uncertaintyA?: number;
  uncertaintyB?: number;
  uncertaintyReported: boolean;
  metricName?: string;
  metricUnit?: string;
}

export const ErrorBarChart: React.FC<ErrorBarChartProps> = ({
  seriesA,
  seriesB,
  valueA,
  valueB,
  uncertaintyA,
  uncertaintyB,
  uncertaintyReported,
  metricName = 'Metric',
  metricUnit = '',
}) => {
  if (valueA == null || valueB == null) {
    return (
      <div className="p-8 text-center text-slate-500 border border-slate-800 rounded-lg bg-slate-900/40">
        Values not verified or insufficient for graphical plotting.
      </div>
    );
  }

  const data = [
    {
      name: seriesA,
      value: valueA,
      errorY: uncertaintyReported && uncertaintyA != null ? uncertaintyA : 0,
      uncertainty: uncertaintyA != null ? `±${uncertaintyA}` : 'not reported',
    },
    {
      name: seriesB,
      value: valueB,
      errorY: uncertaintyReported && uncertaintyB != null ? uncertaintyB : 0,
      uncertainty: uncertaintyB != null ? `±${uncertaintyB}` : 'not reported',
    },
  ];

  return (
    <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
      <div className="flex justify-between items-baseline">
        <h3 className="font-semibold text-slate-200">
          Comparative Analysis: {metricName}
        </h3>
        <span className="text-xs font-mono text-slate-400">
          Unit: {metricUnit || 'standardized'}
        </span>
      </div>

      {!uncertaintyReported ? (
        <div className="p-2.5 rounded bg-amber-950/40 border border-amber-800/40 text-xs text-amber-300 font-medium text-center">
          ⚠️ Uncertainty not reported in source publications. Error bars omitted to prevent ungrounded precision claims.
        </div>
      ) : (
        <div className="text-xs text-emerald-400 font-mono text-right">
          Published experimental uncertainty error bars displayed.
        </div>
      )}

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
            <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }}
              formatter={(val: any, _name: any, item: any) => [
                `${val} ${metricUnit} (${item.payload.uncertainty})`,
                metricName,
              ]}
            />
            <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]}>
              {uncertaintyReported && (
                <ErrorBar dataKey="errorY" width={6} stroke="#f87171" strokeWidth={2} />
              )}
              <Cell fill="#3b82f6" />
              <Cell fill="#6366f1" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
