import React from 'react';
import {
  CheckCircle2,
  Zap,
  Database,
  Sparkles,
  Info,
  ShieldCheck,
  Code2,
} from 'lucide-react';
import type { CompileResponse } from '../types';

interface DiagnosticsPanelProps {
  result: CompileResponse | null;
  isLoading: boolean;
  onOpenTransparency: () => void;
}

export const DiagnosticsPanel: React.FC<DiagnosticsPanelProps> = ({
  result,
  isLoading,
  onOpenTransparency,
}) => {
  if (isLoading) {
    return (
      <div className="glass-panel diagnostics-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
          <Sparkles size={32} color="var(--accent-cyan)" className="spin-icon" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)' }}>
            Smart Routing & Analysis in Progress
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
            Checking local compiler syntax • Querying SQLite response cache
          </p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="glass-panel diagnostics-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', padding: '3rem 1.5rem', color: 'var(--text-dim)' }}>
          <Code2 size={40} style={{ margin: '0 auto 1rem', opacity: 0.6 }} />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            No Analysis Performed Yet
          </h3>
          <p style={{ fontSize: '0.82rem', marginTop: '0.4rem', maxWidth: '300px' }}>
            Click <strong>Compile & Optimize</strong> or pick a preset above to inspect local compiler fixes and AI token savings.
          </p>
        </div>
      </div>
    );
  }

  const {
    status,
    resolution_source,
    diagnostics,
    explanation,
    suggested_fix,
    tokens,
    cache_details,
    request_transparency,
  } = result;

  const isLocal = resolution_source === 'local';
  const isCache = resolution_source === 'cache';
  const isAI = resolution_source === 'ai';
  const isSimulated = resolution_source === 'mock';

  return (
    <div className="glass-panel diagnostics-container">
      <div className="panel-header">
        <div className="panel-title">
          {status === 'passed_locally' && <CheckCircle2 size={18} color="var(--accent-emerald)" />}
          {status === 'resolved_locally' && <ShieldCheck size={18} color="var(--accent-emerald)" />}
          {status === 'cache_hit' && <Database size={18} color="var(--accent-cyan)" />}
          {(status === 'ai_success' || status === 'ai_error') && <Zap size={18} color="var(--accent-violet)" />}
          <span>Optimization & Diagnostics</span>
        </div>

        {/* Resolution Source Badges */}
        <div>
          {isLocal && (
            <span className="badge badge-local">
              <CheckCircle2 size={12} /> Local Resolution (0 AI Tokens)
            </span>
          )}
          {isCache && (
            <span className="badge badge-cache">
              <Database size={12} /> SQLite Cache Hit ({cache_details?.hit_count || 1}x reused)
            </span>
          )}
          {isAI && (
            <span className="badge badge-ai">
              <Sparkles size={12} /> Real AI Response
            </span>
          )}
          {isSimulated && (
            <span className="badge badge-mock">
              <Info size={12} /> Mock Provider (Simulated)
            </span>
          )}
        </div>
      </div>

      <div className="panel-body">
        {/* Diagnostics Badges List */}
        {diagnostics.length > 0 ? (
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Detected Diagnostics ({diagnostics.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {diagnostics.map((d, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.6rem 0.85rem',
                    background: 'rgba(10, 15, 27, 0.6)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span
                      className={`badge ${d.severity === 'error' ? 'badge-error' : 'badge-warning'}`}
                      style={{ fontSize: '0.68rem' }}
                    >
                      {d.category}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
                      Line {d.line}:{d.column}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {d.message}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="result-box local">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#6ee7b7', fontWeight: 600, fontSize: '0.9rem' }}>
              <CheckCircle2 size={16} />
              <span>Clean Code: 0 Diagnostics Detected</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
              Local compiler verified Python syntax. No unnecessary AI API call was dispatched.
            </p>
          </div>
        )}

        {/* Explanation Box */}
        <div className={`result-box ${resolution_source}`}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            Root Cause & Explanation
          </div>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-main)', lineHeight: 1.6 }}>
            {explanation}
          </p>
        </div>

        {/* Suggested Fix */}
        {suggested_fix && (
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
              Proposed Correction
            </div>
            <div className="code-snippet-box">
              {suggested_fix}
            </div>
          </div>
        )}

        {/* Single-Run Savings Summary */}
        <div style={{ padding: '0.85rem 1rem', background: 'rgba(6, 182, 212, 0.05)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
              Optimization on this Compilation:
            </span>
            <strong style={{ color: 'var(--accent-emerald)', fontSize: '0.95rem' }}>
              {tokens.reduction_percentage}% Token Reduction
            </strong>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.35rem', display: 'flex', justifyContent: 'space-between' }}>
            <span>SmartCompile Cost: {tokens.actual_total_tokens} tokens</span>
            <span>Full-File Baseline: {tokens.baseline_tokens} tokens</span>
          </div>
        </div>

        {/* Payload Inspector Button */}
        {request_transparency && (
          <button
            className="btn btn-secondary"
            onClick={onOpenTransparency}
            style={{ width: '100%', borderColor: 'var(--accent-violet)', color: '#c4b5fd' }}
          >
            <Sparkles size={14} />
            <span>View Partial Snippet Sent to AI ({request_transparency.bytes_saved_pct}% payload size reduction)</span>
          </button>
        )}
      </div>
    </div>
  );
};
