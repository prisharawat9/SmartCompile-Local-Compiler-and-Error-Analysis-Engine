import React from 'react';
import {
  Cpu,
  Settings as SettingsIcon,
  Trash2,
  RefreshCw,
  ShieldCheck,
  Eye,
} from 'lucide-react';
import type { HealthResponse } from '../types';

interface HeaderProps {
  health: HealthResponse | null;
  onOpenSettings: () => void;
  onClearCache: () => void;
  onRefresh: () => void;
  onOpenTransparency: () => void;
  hasTransparency: boolean;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  onOpenSettings,
  onClearCache,
  onRefresh,
  onOpenTransparency,
  hasTransparency,
  isRefreshing,
}) => {
  const isMock = health?.is_mock_provider ?? true;
  const providerName = health?.active_ai_provider?.toUpperCase() || 'MOCK';
  const modelName = health?.active_model || 'mock-v1';
  const usingStub = health?.compiler_engine_using_stub ?? true;

  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="brand-section">
          <div className="brand-icon-wrapper">
            <Cpu size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 className="brand-title">SmartCompile</h1>
              <span className="badge badge-local" style={{ fontSize: '0.65rem' }}>
                Module 2
              </span>
            </div>
            <div className="brand-tagline">
              AI Optimization • Local Compiler Routing • Caching
            </div>
          </div>
        </div>

        <div className="header-actions">
          {/* Active AI Provider Status */}
          <div className="status-pill" title={`Active AI Provider: ${providerName} (${modelName})`}>
            <span className={`status-dot ${isMock ? 'mock' : 'active'}`} />
            <span style={{ color: 'var(--text-muted)' }}>AI Provider:</span>
            <strong style={{ color: isMock ? 'var(--accent-amber)' : 'var(--accent-violet)' }}>
              {providerName}
            </strong>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
              ({isMock ? 'Simulated' : modelName})
            </span>
          </div>

          {/* Compiler Status */}
          <div className="status-pill" title={usingStub ? 'Running development AST compiler stub' : "Running Person 1's backend/compiler/analyzer.py"}>
            <ShieldCheck size={14} color="var(--accent-cyan)" />
            <span style={{ color: 'var(--text-muted)' }}>Compiler:</span>
            <strong style={{ color: 'var(--accent-cyan)' }}>
              {usingStub ? 'Dev Stub' : "Person 1 Engine"}
            </strong>
          </div>

          {/* Transparency Trigger */}
          {hasTransparency && (
            <button
              className="btn btn-secondary"
              onClick={onOpenTransparency}
              title="Inspect the exact partial snippet sent to AI"
              style={{ borderColor: 'var(--accent-violet)', color: '#c4b5fd' }}
            >
              <Eye size={15} />
              <span>Inspect AI Payload</span>
            </button>
          )}

          {/* Cache Clear Action */}
          <button
            className="btn btn-secondary"
            onClick={onClearCache}
            title="Clear SQLite response cache"
          >
            <Trash2 size={15} />
            <span>Clear Cache</span>
          </button>

          {/* Settings & Info */}
          <button
            className="btn btn-secondary"
            onClick={onOpenSettings}
            title="Configure AI credentials and review baseline formula"
          >
            <SettingsIcon size={15} />
            <span>Config</span>
          </button>

          {/* Refresh */}
          <button
            className="btn btn-secondary"
            onClick={onRefresh}
            title="Refresh database metrics"
            disabled={isRefreshing}
          >
            <RefreshCw size={15} className={isRefreshing ? 'spin-icon' : ''} />
          </button>
        </div>
      </div>
    </header>
  );
};
