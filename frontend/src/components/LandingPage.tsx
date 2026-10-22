import React, { useState, useEffect, useRef } from 'react';
import './LandingPage.css';

interface LandingPageProps {
  onLogin: (username: string) => void;
}

const STATS = [
  { value: '90%', label: 'Token Reduction' },
  { value: '3-Layer', label: 'Smart Filtering' },
  { value: '0 Tokens', label: 'On Cache Hits' },
  { value: 'Real-time', label: 'Error Analysis' },
];

const FEATURES = [
  {
    icon: '🔍',
    title: 'Local Compiler First',
    desc: 'Lexical, syntax & semantic checks done entirely offline — zero API calls for fixable errors.',
    color: '#10b981',
  },
  {
    icon: '⚡',
    title: 'SQLite Caching',
    desc: 'SHA-256 fingerprinted responses cached persistently. Same error? Instant answer, 0 tokens.',
    color: '#06b6d4',
  },
  {
    icon: '✂️',
    title: 'Snippet Extraction',
    desc: 'When AI is needed, only the relevant ±3 lines are sent — not your entire file.',
    color: '#8b5cf6',
  },
  {
    icon: '📊',
    title: 'Live Token Dashboard',
    desc: 'Real-time savings tracking: actual vs baseline tokens, per-session and cumulative.',
    color: '#f59e0b',
  },
];

// Animated typing effect for the tagline
function TypewriterText({ texts }: { texts: string[] }) {
  const [displayText, setDisplayText] = useState('');
  const [textIdx, setTextIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const current = texts[textIdx];
    let timeout: ReturnType<typeof setTimeout>;

    if (!deleting && charIdx <= current.length) {
      timeout = setTimeout(() => {
        setDisplayText(current.slice(0, charIdx));
        setCharIdx(c => c + 1);
      }, 60);
    } else if (!deleting && charIdx > current.length) {
      timeout = setTimeout(() => setDeleting(true), 1800);
    } else if (deleting && charIdx > 0) {
      timeout = setTimeout(() => {
        setDisplayText(current.slice(0, charIdx - 1));
        setCharIdx(c => c - 1);
      }, 30);
    } else {
      setDeleting(false);
      setTextIdx(i => (i + 1) % texts.length);
    }
    return () => clearTimeout(timeout);
  }, [charIdx, deleting, textIdx, texts]);

  return (
    <span className="typewriter">
      {displayText}
      <span className="typewriter-cursor">|</span>
    </span>
  );
}

// Floating code snippet background
function FloatingCode() {
  const snippets = [
    'def analyze(code): ...',
    'cache_hit = True',
    'tokens_saved += 420',
    'ast.parse(source)',
    'SHA256(snippet)',
    'resolution = "local"',
    'needs_ai = False',
    '✓ Resolved locally',
    'SyntaxError: line 4',
    'fix_applied = True',
    'gemini.generate()',
    'baseline_tokens = 800',
  ];

  return (
    <div className="floating-code-container" aria-hidden="true">
      {snippets.map((s, i) => (
        <div
          key={i}
          className="floating-code-item"
          style={{
            '--delay': `${(i * 1.7) % 12}s`,
            '--duration': `${14 + (i % 4) * 3}s`,
            '--x-start': `${(i * 137) % 90}%`,
            '--opacity': `${0.06 + (i % 3) * 0.03}`,
          } as React.CSSProperties}
        >
          {s}
        </div>
      ))}
    </div>
  );
}

// Login modal
function LoginModal({ onLogin, onClose }: { onLogin: (u: string) => void; onClose: () => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) { setError('Please enter a username.'); return; }
    setIsLoading(true);
    setError('');
    // Simulate auth (replace with real auth if needed)
    await new Promise(r => setTimeout(r, 900));
    setIsLoading(false);
    onLogin(username.trim());
  };

  return (
    <div className="login-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="login-modal" role="dialog" aria-label="Login to SmartCompile">
        <div className="login-glow-ring" />

        <div className="login-header">
          <div className="login-brand-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" fill="url(#lg1)" />
              <path d="M2 17l10 5 10-5" stroke="url(#lg2)" strokeWidth="2" strokeLinecap="round" />
              <path d="M2 12l10 5 10-5" stroke="url(#lg3)" strokeWidth="2" strokeLinecap="round" />
              <defs>
                <linearGradient id="lg1" x1="2" y1="7" x2="22" y2="7">
                  <stop stopColor="#06b6d4" /><stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
                <linearGradient id="lg2" x1="2" y1="17" x2="22" y2="17">
                  <stop stopColor="#06b6d4" /><stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
                <linearGradient id="lg3" x1="2" y1="12" x2="22" y2="12">
                  <stop stopColor="#06b6d4" /><stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h2 className="login-title">Welcome to SmartCompile</h2>
          <p className="login-subtitle">Sign in to access the AI optimization dashboard</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="sc-username">Username</label>
            <input
              id="sc-username"
              ref={inputRef}
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter your username"
              autoComplete="username"
              className="login-input"
            />
          </div>
          <div className="login-field">
            <label htmlFor="sc-password">Password</label>
            <input
              id="sc-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              className="login-input"
            />
          </div>

          {error && <div className="login-error" role="alert">{error}</div>}

          <button
            id="sc-login-submit"
            type="submit"
            className={`login-btn${isLoading ? ' loading' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="login-spinner" />
            ) : (
              <>
                <span>Sign In</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </>
            )}
          </button>

          <p className="login-demo-hint">
            💡 Demo: any username works — no backend auth required
          </p>
        </form>

        <button className="login-close" onClick={onClose} aria-label="Close login">✕</button>
      </div>
    </div>
  );
}

export function LandingPage({ onLogin }: LandingPageProps) {
  const [showLogin, setShowLogin] = useState(false);
  const [visibleStats, setVisibleStats] = useState(false);
  const [visibleFeatures, setVisibleFeatures] = useState<boolean[]>(FEATURES.map(() => false));
  const statsRef = useRef<HTMLDivElement>(null);
  const featuresRef = useRef<HTMLDivElement[]>([]);

  // Intersection observers for scroll-in animations
  useEffect(() => {
    const statsObs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisibleStats(true); },
      { threshold: 0.2 }
    );
    if (statsRef.current) statsObs.observe(statsRef.current);

    const featureObs = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          const idx = featuresRef.current.indexOf(entry.target as HTMLDivElement);
          if (entry.isIntersecting && idx !== -1) {
            setTimeout(() => {
              setVisibleFeatures(prev => {
                const next = [...prev];
                next[idx] = true;
                return next;
              });
            }, idx * 120);
          }
        });
      },
      { threshold: 0.15 }
    );
    featuresRef.current.forEach(el => { if (el) featureObs.observe(el); });

    return () => { statsObs.disconnect(); featureObs.disconnect(); };
  }, []);

  return (
    <div className="landing-root">
      <FloatingCode />

      {/* ── NAV ── */}
      <nav className="landing-nav">
        <div className="nav-brand">
          <div className="nav-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" fill="url(#navGrad)" />
              <path d="M2 17l10 5 10-5M2 12l10 5 10-5" stroke="url(#navGrad2)" strokeWidth="2" strokeLinecap="round" />
              <defs>
                <linearGradient id="navGrad"><stop stopColor="#06b6d4" /><stop offset="1" stopColor="#8b5cf6" /></linearGradient>
                <linearGradient id="navGrad2"><stop stopColor="#06b6d4" /><stop offset="1" stopColor="#8b5cf6" /></linearGradient>
              </defs>
            </svg>
          </div>
          <span className="nav-brand-name">SmartCompile</span>
        </div>
        <button
          id="landing-login-nav"
          className="nav-login-btn"
          onClick={() => setShowLogin(true)}
        >
          Sign In →
        </button>
      </nav>

      {/* ── HERO ── */}
      <section className="hero-section">
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          AI-Powered Error Analysis Engine
        </div>

        <h1 className="hero-title">
          Compile Smarter.<br />
          <span className="hero-gradient-text">Spend Less.</span>
        </h1>

        <p className="hero-subtitle">
          <TypewriterText texts={[
            'Fix syntax errors locally — 0 tokens spent.',
            'Cache repeat answers — 0 AI calls needed.',
            'Send only relevant snippets to AI.',
            'Track every token saved in real-time.',
          ]} />
        </p>

        <p className="hero-description">
          SmartCompile is a 3-layer intelligent compiler pipeline that catches and fixes Python errors
          <strong> locally first</strong>, caches AI responses persistently, and only sends the
          <strong> minimum necessary code</strong> to AI when truly needed — saving up to 90% on API token costs.
        </p>

        <div className="hero-actions">
          <button
            id="landing-cta-primary"
            className="cta-primary"
            onClick={() => setShowLogin(true)}
          >
            <span>Get Started</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <a href="#how-it-works" className="cta-secondary">
            How it works ↓
          </a>
        </div>

        {/* Animated code preview */}
        <div className="hero-code-preview">
          <div className="code-preview-header">
            <span className="dot red" /><span className="dot yellow" /><span className="dot green" />
            <span className="code-preview-filename">example.py</span>
          </div>
          <pre className="code-preview-body"><code>{`def calculate_discount(price, customer_tier)  # ← missing colon
    if customer_tier == "gold"                 # ← missing colon
        return price * 0.8
    return price

`}<span className="code-result">✓ <span className="code-result-local">Resolved locally</span> — 0 tokens used</span></code></pre>
        </div>
      </section>

      {/* ── STATS STRIP ── */}
      <section className="stats-section" ref={statsRef}>
        {STATS.map((s, i) => (
          <div
            key={i}
            className={`stat-item${visibleStats ? ' visible' : ''}`}
            style={{ transitionDelay: `${i * 100}ms` }}
          >
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="features-section" id="how-it-works">
        <div className="section-header">
          <h2 className="section-title">How SmartCompile Works</h2>
          <p className="section-subtitle">
            Three intelligent layers that progressively minimize AI token usage
          </p>
        </div>

        <div className="features-grid">
          {FEATURES.map((f, i) => (
            <div
              key={i}
              ref={el => { if (el) featuresRef.current[i] = el; }}
              className={`feature-card${visibleFeatures[i] ? ' visible' : ''}`}
              style={{
                '--feature-color': f.color,
                transitionDelay: `${i * 80}ms`,
              } as React.CSSProperties}
            >
              <div className="feature-icon-wrap">
                <span className="feature-icon">{f.icon}</span>
              </div>
              <h3 className="feature-title">{f.title}</h3>
              <p className="feature-desc">{f.desc}</p>
              <div className="feature-glow" />
            </div>
          ))}
        </div>
      </section>

      {/* ── PIPELINE DIAGRAM ── */}
      <section className="pipeline-section">
        <h2 className="section-title" style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          The Optimization Pipeline
        </h2>
        <div className="pipeline-track">
          {[
            { step: '01', label: 'Local Compiler', sub: 'Syntax + Semantic', color: '#10b981', icon: '🔍' },
            { step: '02', label: 'Auto-Fix', sub: 'Deterministic repair', color: '#06b6d4', icon: '🔧' },
            { step: '03', label: 'Cache Lookup', sub: 'SHA-256 match', color: '#8b5cf6', icon: '⚡' },
            { step: '04', label: 'Snippet AI', sub: 'Minimal tokens', color: '#f59e0b', icon: '🤖' },
          ].map((p, i, arr) => (
            <React.Fragment key={i}>
              <div className="pipeline-step" style={{ '--pipe-color': p.color } as React.CSSProperties}>
                <div className="pipeline-step-num">{p.step}</div>
                <div className="pipeline-icon">{p.icon}</div>
                <div className="pipeline-label">{p.label}</div>
                <div className="pipeline-sub">{p.sub}</div>
              </div>
              {i < arr.length - 1 && (
                <div className="pipeline-arrow">→</div>
              )}
            </React.Fragment>
          ))}
        </div>
        <p className="pipeline-note">
          Each layer short-circuits early — most errors never reach the AI.
        </p>
      </section>

      {/* ── CTA BANNER ── */}
      <section className="cta-section">
        <div className="cta-banner">
          <div className="cta-banner-glow" />
          <h2 className="cta-banner-title">Ready to compile smarter?</h2>
          <p className="cta-banner-sub">
            Start analysing code with up to 90% fewer tokens. No configuration needed.
          </p>
          <button
            id="landing-cta-bottom"
            className="cta-primary large"
            onClick={() => setShowLogin(true)}
          >
            Open Dashboard →
          </button>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="landing-footer">
        <span className="footer-brand">SmartCompile</span>
        <span className="footer-sep">·</span>
        <span className="footer-tagline">AI Error Analysis Engine · Token Optimized</span>
      </footer>

      {/* LOGIN MODAL */}
      {showLogin && (
        <LoginModal
          onLogin={onLogin}
          onClose={() => setShowLogin(false)}
        />
      )}
    </div>
  );
}
