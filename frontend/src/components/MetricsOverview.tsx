import React from 'react';
import {
  Zap,
  Database,
  Coins,
  TrendingDown,
  Layers,
} from 'lucide-react';
import type { StatsResponse } from '../types';

interface MetricsOverviewProps {
  stats: StatsResponse | null;
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ stats }) => {
  const totalCompilations = stats?.total_compilations ?? 0;
  const localResolutions = stats?.resolutions?.local ?? 0;
  const cacheHits = stats?.cache?.total_hits ?? 0;
  const hitRate = stats?.cache?.hit_rate_percentage ?? 0;
  const realAiCalls = stats?.real_ai?.calls ?? 0;
  const mockCalls = stats?.simulated_mock?.calls ?? 0;

  const actualTokens = stats?.real_ai?.total_tokens ?? 0;
  const simTokens = stats?.simulated_mock?.total_simulated_tokens ?? 0;

  const tokensSaved = stats?.savings?.total_tokens_saved ?? 0;
  const reductionPct = stats?.savings?.percentage_reduction ?? 0;
  const baselineTokens = stats?.savings?.baseline_tokens ?? 0;

  return (
    <div className="metrics-grid">
      {/* 1. Total Compilations & Resolution Breakdown */}
      <div className="glass-panel metric-card">
        <div className="metric-header">
          <span className="metric-title">Compilations</span>
          <Layers size={18} className="metric-icon" />
        </div>
        <div className="metric-value">{totalCompilations}</div>
        <div className="metric-subtext">
          <span style={{ color: 'var(--accent-emerald)' }}>{localResolutions} Local</span> •{' '}
          <span style={{ color: 'var(--accent-cyan)' }}>{cacheHits} Cache</span> •{' '}
          <span style={{ color: 'var(--accent-violet)' }}>{realAiCalls + mockCalls} AI</span>
        </div>
      </div>

      {/* 2. Cache Hit Performance */}
      <div className="glass-panel metric-card">
        <div className="metric-header">
          <span className="metric-title">Cache Hit Rate</span>
          <Database size={18} style={{ color: 'var(--accent-cyan)' }} />
        </div>
        <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
          {hitRate}%
        </div>
        <div className="metric-subtext">
          <strong>{cacheHits}</strong> hits from {stats?.cache?.total_lookups ?? 0} lookups ({stats?.cache?.total_entries ?? 0} cached)
        </div>
      </div>

      {/* 3. AI API Requests */}
      <div className="glass-panel metric-card">
        <div className="metric-header">
          <span className="metric-title">AI Provider Calls</span>
          <Zap size={18} style={{ color: 'var(--accent-violet)' }} />
        </div>
        <div className="metric-value">
          {realAiCalls}
          {mockCalls > 0 && (
            <span style={{ fontSize: '0.9rem', color: 'var(--accent-amber)', marginLeft: '0.4rem', fontWeight: 500 }}>
              (+{mockCalls} mock)
            </span>
          )}
        </div>
        <div className="metric-subtext">
          {mockCalls > 0 ? (
            <span style={{ color: 'var(--accent-amber)' }}>
              Mock calls excluded from billing totals
            </span>
          ) : (
            'Zero calls on clean/cached code'
          )}
        </div>
      </div>

      {/* 4. Provider Tokens Used */}
      <div className="glass-panel metric-card">
        <div className="metric-header">
          <span className="metric-title">Actual Provider Tokens</span>
          <Coins size={18} style={{ color: 'var(--accent-amber)' }} />
        </div>
        <div className="metric-value" style={{ color: actualTokens > 0 ? 'var(--text-main)' : 'var(--text-muted)' }}>
          {actualTokens.toLocaleString()}
        </div>
        <div className="metric-subtext">
          {simTokens > 0 ? (
            <span>
              Simulated: <strong style={{ color: 'var(--accent-amber)' }}>{simTokens.toLocaleString()}</strong> tokens
            </span>
          ) : (
            'Reported directly by AI provider API'
          )}
        </div>
      </div>

      {/* 5. Tokens Saved vs Full-File Baseline */}
      <div className="glass-panel metric-card" style={{ borderColor: 'rgba(16, 185, 129, 0.35)' }}>
        <div className="metric-header">
          <span className="metric-title">
            Token Savings (ESTIMATED{mockCalls > 0 && realAiCalls === 0 ? ' - Simulated' : ''})
          </span>
          <TrendingDown size={18} style={{ color: 'var(--accent-emerald)' }} />
        </div>
        <div className="metric-value metric-highlight">
          {reductionPct}%
        </div>
        <div className="metric-subtext">
          Saved <strong style={{ color: 'var(--accent-emerald)' }}>{tokensSaved.toLocaleString()}</strong> of {baselineTokens.toLocaleString()} baseline tokens
          {mockCalls > 0 && (
            <span style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Includes {mockCalls} simulated runs vs baseline
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
