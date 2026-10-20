import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import type { StatsResponse } from '../types';
import { BarChart3, PieChart as PieChartIcon } from 'lucide-react';

interface AnalyticsChartsProps {
  stats: StatsResponse | null;
}

const RESOLUTION_COLORS = {
  local: '#10b981', // Emerald
  cache: '#06b6d4', // Cyan
  ai: '#8b5cf6',    // Violet
  mock: '#f59e0b',  // Amber
};

export const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ stats }) => {
  const totalCompilations = stats?.total_compilations ?? 0;

  if (totalCompilations === 0) {
    return (
      <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-dim)' }}>
        <BarChart3 size={36} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
        <h4 style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>No Compilation Telemetry Yet</h4>
        <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
          Run your first compilation using the editor above to generate live charts.
        </p>
      </div>
    );
  }

  // 1. Resolution Breakdown Data
  const resolutionData = [
    { name: 'Local Compiler', count: stats?.resolutions?.local ?? 0, fill: RESOLUTION_COLORS.local },
    { name: 'SQLite Cache', count: stats?.resolutions?.cache ?? 0, fill: RESOLUTION_COLORS.cache },
    { name: 'Real AI API', count: stats?.real_ai?.calls ?? 0, fill: RESOLUTION_COLORS.ai },
    { name: 'Mock AI', count: stats?.simulated_mock?.calls ?? 0, fill: RESOLUTION_COLORS.mock },
  ].filter((d) => d.count > 0);

  // 2. Token Comparison: Baseline vs Actual
  const baselineTokens = stats?.savings?.baseline_tokens ?? 0;
  const actualTokens = (stats?.real_ai?.total_tokens ?? 0) + (stats?.simulated_mock?.total_simulated_tokens ?? 0);
  const savedTokens = stats?.savings?.total_tokens_saved ?? 0;

  const tokenComparisonData = [
    {
      category: 'Tokens',
      'Baseline (Naive Full File)': baselineTokens,
      'SmartCompile Consumed': actualTokens,
      'Tokens Saved': savedTokens,
    },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
      {/* Chart 1: Resolution Breakdown Donut */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <PieChartIcon size={16} color="var(--accent-cyan)" />
          <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)' }}>
            Resolution Source Distribution
          </h4>
        </div>
        <div style={{ width: '100%', height: '240px' }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={resolutionData}
                dataKey="count"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={4}
              >
                {resolutionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} stroke="rgba(0,0,0,0.5)" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d121f',
                  borderColor: 'rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  fontSize: '0.8rem',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '0.78rem' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: Baseline vs SmartCompile Tokens */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <BarChart3 size={16} color="var(--accent-emerald)" />
          <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)' }}>
            Token Efficiency vs Baseline
          </h4>
        </div>
        <div style={{ width: '100%', height: '240px' }}>
          <ResponsiveContainer>
            <BarChart data={tokenComparisonData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <XAxis dataKey="category" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d121f',
                  borderColor: 'rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  fontSize: '0.8rem',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '0.78rem' }} />
              <Bar dataKey="Baseline (Naive Full File)" fill="#64748b" radius={[4, 4, 0, 0]} />
              <Bar dataKey="SmartCompile Consumed" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Tokens Saved" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
