import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { MetricsOverview } from './components/MetricsOverview';
import { EditorWorkspace } from './components/EditorWorkspace';
import { DiagnosticsPanel } from './components/DiagnosticsPanel';
import { AnalyticsCharts } from './components/AnalyticsCharts';
import { HistoryTable } from './components/HistoryTable';
import { TransparencyModal } from './components/TransparencyModal';
import { SettingsModal } from './components/SettingsModal';
import { LandingPage } from './components/LandingPage';
import { SplashCursor } from './components/SplashCursor';

import {
  compileCode,
  fetchStats,
  fetchHistory,
  fetchHealth,
  clearCache,
} from './api';

import type {
  CompileResponse,
  StatsResponse,
  HistoryItem,
  HealthResponse,
  TransparencyDetails,
} from './types';

const INITIAL_CODE = `def calculate_discount(price, customer_tier)
    # Missing colon above and below!
    if customer_tier == "gold"
        return price * 0.8
    elif customer_tier == "silver"
        return price * 0.9
    return price

final_price = calculate_discount(100, "gold")
print("Discounted price:", final_price)
`;

export const App: React.FC = () => {
  const [sourceCode, setSourceCode] = useState<string>(INITIAL_CODE);
  const [forceAi, setForceAi] = useState<boolean>(false);
  const [compileResult, setCompileResult] = useState<CompileResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyTotal, setHistoryTotal] = useState<number>(0);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // Modals
  const [isTransparencyOpen, setIsTransparencyOpen] = useState<boolean>(false);
  const [activeTransparency, setActiveTransparency] = useState<TransparencyDetails | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [loggedIn, setLoggedIn] = useState<boolean>(false);
  const [username, setUsername] = useState<string>('');

  // Initial load
  const loadDashboardData = async () => {
    setIsRefreshing(true);
    try {
      const [statsData, histData, healthData] = await Promise.all([
        fetchStats().catch(() => null),
        fetchHistory(15, 0).catch(() => ({ items: [], total: 0 })),
        fetchHealth().catch(() => null),
      ]);
      if (statsData) setStats(statsData);
      if (histData) {
        setHistory(histData.items);
        setHistoryTotal(histData.total);
      }
      if (healthData) setHealth(healthData);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleCompile = async () => {
    if (!sourceCode.trim()) return;
    setIsLoading(true);
    setErrorBanner(null);

    try {
      const res = await compileCode({
        source_code: sourceCode,
        language: 'python',
        force_ai: forceAi,
      });
      setCompileResult(res);
      if (res.request_transparency) {
        setActiveTransparency(res.request_transparency);
      }
      // Refresh stats and history in background
      await loadDashboardData();
    } catch (err: any) {
      setErrorBanner(err.message || 'Compilation failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyFix = () => {
    if (compileResult?.corrected_code) {
      setSourceCode(compileResult.corrected_code);
    }
  };

  const handleClearCacheAction = async () => {
    await clearCache();
    await loadDashboardData();
  };

  return (
    <>
      <SplashCursor />
      {loggedIn ? (
        <div className="app-container">
          <Header
            health={health}
            onOpenSettings={() => setIsSettingsOpen(true)}
            onClearCache={() => setIsSettingsOpen(true)}
            onRefresh={loadDashboardData}
            onOpenTransparency={() => setIsTransparencyOpen(true)}
            hasTransparency={Boolean(activeTransparency)}
            isRefreshing={isRefreshing}
          />

          <main className="main-content">
            {errorBanner && (
              <div
                style={{
                  padding: '0.85rem 1.25rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(244, 63, 94, 0.15)',
                  border: '1px solid var(--accent-rose)',
                  color: '#fda4af',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '0.88rem',
                }}
              >
                <div>
                  <strong>Error:</strong> {errorBanner}
                </div>
                <button
                  onClick={() => setErrorBanner(null)}
                  style={{ background: 'none', border: 'none', color: '#fda4af', cursor: 'pointer', fontWeight: 700 }}
                >
                  ✕
                </button>
              </div>
            )}

            <MetricsOverview stats={stats} />

            <div className="workspace-grid">
              <EditorWorkspace
                sourceCode={sourceCode}
                setSourceCode={setSourceCode}
                onCompile={handleCompile}
                isLoading={isLoading}
                forceAi={forceAi}
                setForceAi={setForceAi}
                correctedCode={compileResult?.corrected_code ?? null}
                onApplyFix={handleApplyFix}
              />
              <DiagnosticsPanel
                result={compileResult}
                isLoading={isLoading}
                onOpenTransparency={() => setIsTransparencyOpen(true)}
              />
            </div>

            <AnalyticsCharts stats={stats} />

            <HistoryTable
              items={history}
              total={historyTotal}
              onInspectPayload={(t) => {
                setActiveTransparency(t);
                setIsTransparencyOpen(true);
              }}
              onLoadCode={(code) => setSourceCode(code)}
            />
          </main>

          <TransparencyModal
            isOpen={isTransparencyOpen}
            onClose={() => setIsTransparencyOpen(false)}
            transparency={activeTransparency}
          />

          <SettingsModal
            isOpen={isSettingsOpen}
            onClose={() => setIsSettingsOpen(false)}
            health={health}
            onClearCache={handleClearCacheAction}
          />
        </div>
      ) : (
        <LandingPage onLogin={(user) => { setUsername(user); setLoggedIn(true); }} />
      )}
    </>
  );
};

export default App;
