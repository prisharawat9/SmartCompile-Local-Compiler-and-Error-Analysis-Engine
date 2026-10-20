import React, { useState } from 'react';
import {
  X,
  Settings as SettingsIcon,
  Shield,
  KeyRound,
  Trash2,
  CheckCircle2,
} from 'lucide-react';
import type { HealthResponse } from '../types';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  health: HealthResponse | null;
  onClearCache: () => Promise<void>;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  health,
  onClearCache,
}) => {
  const [clearing, setClearing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleClear = async () => {
    setClearing(true);
    try {
      await onClearCache();
      setMessage('Persistent cache cleared successfully.');
      setConfirmDelete(false);
      setTimeout(() => setMessage(null), 3500);
    } catch (err: any) {
      setMessage(`Failed to clear cache: ${err.message}`);
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '640px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <SettingsIcon size={20} color="var(--accent-cyan)" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
              System Configuration & AI Provider
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
          {message && (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#6ee7b7',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                fontSize: '0.85rem',
              }}
            >
              {message}
            </div>
          )}

          {/* AI Provider Section */}
          <div className="result-box" style={{ background: 'rgba(10, 15, 27, 0.6)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <KeyRound size={16} color="var(--accent-violet)" />
              <strong style={{ fontSize: '0.9rem' }}>Active AI Provider</strong>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.82rem' }}>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Provider:</span>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '0.15rem' }}>
                  {health?.active_ai_provider.toUpperCase()}
                </div>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Model:</span>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '0.15rem' }}>
                  {health?.active_model}
                </div>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>API Key Status:</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.15rem' }}>
                  <span
                    className={`status-dot ${health?.api_key_configured ? 'active' : 'mock'}`}
                  />
                  <span>{health?.api_key_configured ? 'Configured (Active)' : 'Not Set (Using Mock)'}</span>
                </div>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Database:</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.15rem', color: '#6ee7b7' }}>
                  <CheckCircle2 size={13} />
                  <span>SQLite Connected</span>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '0.85rem', padding: '0.65rem 0.85rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <Shield size={13} style={{ display: 'inline', marginRight: '0.35rem', verticalAlign: 'middle', color: '#6ee7b7' }} />
              Security Guarantee: API keys are strictly read server-side from environment variables. Secrets are never exposed to browser or client bundles.
            </div>
          </div>

          {/* Instructions for Switching to Live API */}
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.3rem' }}>
              How to configure live OpenAI / Gemini / Anthropic:
            </div>
            <ol style={{ paddingLeft: '1.25rem', lineHeight: 1.6 }}>
              <li>Copy <code>.env.example</code> to <code>.env</code> in the project root.</li>
              <li>Set <code>AI_PROVIDER=openai</code> (or <code>gemini</code> / <code>anthropic</code>).</li>
              <li>Provide your key, e.g. <code>OPENAI_API_KEY=sk-...</code></li>
              <li>Restart the FastAPI backend. Real provider usage will begin immediately.</li>
            </ol>
          </div>

          {/* Baseline Definition */}
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
            <strong style={{ color: 'var(--text-muted)' }}>Baseline Formula Documentation:</strong>
            <p style={{ marginTop: '0.25rem', lineHeight: 1.5 }}>
              SmartCompile compares actual tokens against a clearly defined Full-File Baseline: sending the entire code file plus 250 prompt overhead tokens and 180 expected completion tokens on every run.
            </p>
          </div>

          {/* Cache Management */}
          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <strong style={{ fontSize: '0.88rem', color: 'var(--text-main)' }}>Clear Persistent Response Cache</strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '0.15rem' }}>
                  Wipes all stored AI completions from SQLite, forcing future unresolved queries to re-evaluate.
                </p>
              </div>

              {!confirmDelete ? (
                <button
                  className="btn btn-danger"
                  onClick={() => setConfirmDelete(true)}
                  style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
                >
                  <Trash2 size={14} />
                  <span>Clear Cache...</span>
                </button>
              ) : (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => setConfirmDelete(false)}
                    style={{ padding: '0.35rem 0.65rem', fontSize: '0.78rem' }}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={handleClear}
                    disabled={clearing}
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
                  >
                    {clearing ? 'Clearing...' : 'Confirm Clear'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
