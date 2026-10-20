import React from 'react';
import type { HistoryItem, TransparencyDetails } from '../types';
import { History, Eye, ArrowUpRight, CheckCircle2, Database, Zap } from 'lucide-react';

interface HistoryTableProps {
  items: HistoryItem[];
  total: number;
  onInspectPayload: (transparency: TransparencyDetails) => void;
  onLoadCode: (code: string) => void;
}

export const HistoryTable: React.FC<HistoryTableProps> = ({
  items,
  total,
  onInspectPayload,
  onLoadCode,
}) => {
  if (items.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-dim)' }}>
        <History size={32} style={{ margin: '0 auto 0.5rem', opacity: 0.5 }} />
        <h4 style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No Compilation History</h4>
        <p style={{ fontSize: '0.78rem' }}>Runs are automatically stored in the SQLite database.</p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ overflow: 'hidden' }}>
      <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <History size={16} color="var(--accent-cyan)" />
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Recent Compilation Log</h4>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
          Showing {items.length} of {total} records
        </span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="history-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Status</th>
              <th>Resolution Source</th>
              <th>Provider / Model</th>
              <th>Tokens Saved</th>
              <th>Baseline</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const dateStr = new Date(item.timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              });

              return (
                <tr key={item.id}>
                  <td style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {dateStr}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        item.status.includes('error') ? 'badge-error' : 'badge-local'
                      }`}
                      style={{ fontSize: '0.68rem' }}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td>
                    {item.resolution_source === 'local' && (
                      <span style={{ color: '#6ee7b7', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <CheckCircle2 size={13} /> Local Compiler
                      </span>
                    )}
                    {item.resolution_source === 'cache' && (
                      <span style={{ color: '#67e8f9', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Database size={13} /> Cache Hit
                      </span>
                    )}
                    {item.resolution_source === 'ai' && (
                      <span style={{ color: '#c4b5fd', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Zap size={13} /> Real AI
                      </span>
                    )}
                    {item.resolution_source === 'mock' && (
                      <span style={{ color: '#fde68a', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        Mock Simulation
                      </span>
                    )}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {item.ai_provider ? `${item.ai_provider} (${item.ai_model || 'default'})` : 'N/A (Bypassed)'}
                  </td>
                  <td style={{ color: 'var(--accent-emerald)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    +{item.estimated_tokens_saved.toLocaleString()}
                  </td>
                  <td style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {item.baseline_tokens.toLocaleString()}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      {item.request_transparency && (
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem' }}
                          title="Inspect partial snippet sent to AI"
                          onClick={() => onInspectPayload(item.request_transparency!)}
                        >
                          <Eye size={12} />
                          <span>Payload</span>
                        </button>
                      )}
                      {item.source_preview && (
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem' }}
                          title="Load code snippet into editor"
                          onClick={() => onLoadCode(item.source_preview)}
                        >
                          <ArrowUpRight size={12} />
                          <span>Load</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
