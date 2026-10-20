import React from 'react';
import { X, Eye, ShieldCheck } from 'lucide-react';
import type { TransparencyDetails } from '../types';

interface TransparencyModalProps {
  isOpen: boolean;
  onClose: () => void;
  transparency: TransparencyDetails | null;
}

export const TransparencyModal: React.FC<TransparencyModalProps> = ({
  isOpen,
  onClose,
  transparency,
}) => {
  if (!isOpen || !transparency) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Eye size={20} color="var(--accent-violet)" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
              AI Request Transparency Inspector
            </h3>
          </div>
          <button
            className="btn btn-secondary"
            onClick={onClose}
            style={{ padding: '0.35rem', borderRadius: '50%' }}
          >
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {/* Savings Metric Header */}
          <div
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.1))',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Payload Size Reduction
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#c4b5fd' }}>
                {transparency.bytes_saved_pct}% Payload Trimmed
              </div>
            </div>
            <div style={{ textAlign: 'right', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              <div>Full File: <strong>{transparency.full_file_char_count}</strong> chars</div>
              <div>Snippet Sent: <strong style={{ color: 'var(--accent-cyan)' }}>{transparency.snippet_char_count}</strong> chars</div>
            </div>
          </div>

          {/* Privacy & Efficiency Guarantee */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: '#6ee7b7' }}>
            <ShieldCheck size={16} />
            <span>
              Zero project secrets or surrounding files were transmitted. Only lines {transparency.line_start} to {transparency.line_end} were submitted.
            </span>
          </div>

          {/* Section 1: Exact Snippet Sent */}
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
              Focused Snippet (Lines {transparency.line_start} - {transparency.line_end})
            </div>
            <div className="code-snippet-box" style={{ maxHeight: '200px' }}>
              {transparency.snippet_sent}
            </div>
          </div>

          {/* Section 2: System Prompt */}
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
              System Prompt
            </div>
            <div
              style={{
                background: '#090d16',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {transparency.system_prompt}
            </div>
          </div>

          {/* Section 3: User Prompt */}
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
              User Prompt Dispatched
            </div>
            <div className="code-snippet-box" style={{ maxHeight: '160px', color: '#93c5fd' }}>
              {transparency.user_prompt}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
