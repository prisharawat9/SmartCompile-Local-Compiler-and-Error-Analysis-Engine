import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import {
  Play,
  RotateCcw,
  Copy,
  Check,
  Wand2,
  AlertTriangle,
  FileCode2,
} from 'lucide-react';

interface EditorWorkspaceProps {
  sourceCode: string;
  setSourceCode: (code: string) => void;
  onCompile: () => void;
  isLoading: boolean;
  forceAi: boolean;
  setForceAi: (force: boolean) => void;
  correctedCode: string | null;
  onApplyFix: () => void;
}

const CODE_PRESETS = [
  {
    name: '1. Clean Code (0 AI Calls)',
    desc: 'Valid Python function. Passes local compiler analysis; AI call is bypassed completely.',
    code: `def calculate_fibonacci(n: int) -> list[int]:
    """Return Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence[:n]

print(calculate_fibonacci(8))
`,
  },
  {
    name: '2. Local Fixable Syntax (0 AI Calls)',
    desc: 'Missing colons after def and if statements. Handled deterministically by compiler without calling AI.',
    code: `def calculate_discount(price, customer_tier)
    # Missing colon above and below!
    if customer_tier == "gold"
        return price * 0.8
    elif customer_tier == "silver"
        return price * 0.9
    return price

final_price = calculate_discount(100, "gold")
print("Discounted:", final_price)
`,
  },
  {
    name: '3. ZeroDivision Runtime Bug (Routes Snippet to AI)',
    desc: 'Unresolved logic flaw. Extracts ONLY lines around the division and queries AI/cache.',
    code: `def compute_averages(data_points: list[float]) -> float:
    total_sum = sum(data_points)
    count = len(data_points)
    
    # Bug: When data_points is empty, count is 0!
    average = total_sum / count
    return average

empty_result = compute_averages([])
print(empty_result)
`,
  },
  {
    name: '4. Undefined NameError (Routes Snippet to AI)',
    desc: 'Undefined variable bug. Compiler extracts focused snippet and queries AI model.',
    code: `import math

def process_coordinates(x: float, y: float) -> float:
    distance = math.sqrt(x**2 + y**2)
    # Bug: scaling_factor is referenced but never initialized
    adjusted = distance * scaling_factor
    return adjusted

print(process_coordinates(3.0, 4.0))
`,
  },
  {
    name: '5. Repeated Run (Instant Cache Hit)',
    desc: 'Compiling the same snippet twice retrieves answer instantly from SQLite cache with 0 AI tokens.',
    code: `def parse_user_payload(raw_json):
    try:
        data = raw_json["metadata"]["user_id"]
    except KeyError:
        data = None
    return data
`,
  },
];

export const EditorWorkspace: React.FC<EditorWorkspaceProps> = ({
  sourceCode,
  setSourceCode,
  onCompile,
  isLoading,
  forceAi,
  setForceAi,
  correctedCode,
  onApplyFix,
}) => {
  const [copied, setCopied] = useState(false);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'editor' | 'preview'>('editor');

  const handleCopy = () => {
    navigator.clipboard.writeText(sourceCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePresetSelect = (presetCode: string) => {
    setSourceCode(presetCode);
  };

  const handleConfirmApply = () => {
    onApplyFix();
    setShowApplyModal(false);
    setActiveTab('editor');
  };

  return (
    <div className="glass-panel editor-container">
      {/* Top Editor Toolbar */}
      <div className="editor-toolbar">
        <div className="toolbar-group">
          <FileCode2 size={16} color="var(--accent-cyan)" />
          <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>Source Editor</span>
          <select
            className="select-input"
            defaultValue="python"
            disabled
            title="Initial prototype supports Python 3.11"
          >
            <option value="python">Python 3.11</option>
          </select>

          {/* Test Case Presets */}
          <select
            className="select-input"
            onChange={(e) => {
              const preset = CODE_PRESETS.find((p) => p.name === e.target.value);
              if (preset) handlePresetSelect(preset.code);
            }}
            defaultValue=""
          >
            <option value="" disabled>
              Select Demonstration Test Preset...
            </option>
            {CODE_PRESETS.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        <div className="toolbar-group">
          {/* Force AI Toggle */}
          <label className="toggle-label" title="Force AI analysis even if code passes local syntax checks">
            <input
              type="checkbox"
              className="toggle-checkbox"
              checked={forceAi}
              onChange={(e) => setForceAi(e.target.checked)}
            />
            <span>Deep AI Explanation</span>
          </label>

          {/* Copy Button */}
          <button className="btn btn-secondary" onClick={handleCopy} title="Copy code to clipboard">
            {copied ? <Check size={14} color="var(--accent-emerald)" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Clear Button */}
          <button
            className="btn btn-secondary"
            onClick={() => setSourceCode('')}
            title="Clear editor contents"
          >
            <RotateCcw size={14} />
            <span>Clear</span>
          </button>

          {/* Primary Action Button */}
          <button
            className="btn btn-primary"
            onClick={onCompile}
            disabled={isLoading || !sourceCode.trim()}
          >
            {isLoading ? (
              <>
                <RotateCcw size={15} className="spin-icon" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Play size={15} />
                <span>Compile & Optimize</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Editor Surface or Fix Preview Tabs */}
      {correctedCode && correctedCode !== sourceCode && (
        <div style={{ display: 'flex', background: 'rgba(10, 15, 27, 0.95)', borderBottom: '1px solid var(--border-subtle)', padding: '0.4rem 1.25rem', gap: '0.5rem' }}>
          <button
            className={`btn ${activeTab === 'editor' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.3rem 0.8rem', fontSize: '0.78rem' }}
            onClick={() => setActiveTab('editor')}
          >
            Current Code
          </button>
          <button
            className={`btn ${activeTab === 'preview' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.3rem 0.8rem', fontSize: '0.78rem' }}
            onClick={() => setActiveTab('preview')}
          >
            <Wand2 size={13} />
            Proposed Correction
          </button>
        </div>
      )}

      <div className="editor-surface">
        {activeTab === 'editor' ? (
          <Editor
            height="500px"
            language="python"
            theme="vs-dark"
            value={sourceCode}
            onChange={(val) => setSourceCode(val || '')}
            options={{
              fontSize: 13.5,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              wordWrap: 'on',
              lineNumbers: 'on',
              renderLineHighlight: 'all',
              tabSize: 4,
            }}
          />
        ) : (
          <Editor
            height="500px"
            language="python"
            theme="vs-dark"
            value={correctedCode || ''}
            options={{
              fontSize: 13.5,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              readOnly: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
            }}
          />
        )}
      </div>

      {/* Proposed Fix Bar */}
      {correctedCode && correctedCode !== sourceCode && (
        <div className="fix-preview-container">
          <div className="fix-preview-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Wand2 size={16} color="var(--accent-emerald)" />
              <strong style={{ fontSize: '0.85rem', color: '#6ee7b7' }}>
                Correction Available
              </strong>
            </div>
            <button
              className="btn btn-primary"
              style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}
              onClick={() => setShowApplyModal(true)}
            >
              <Check size={14} />
              <span>Apply Proposed Fix</span>
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Modal before replacing source code */}
      {showApplyModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '540px' }}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <AlertTriangle size={20} color="var(--accent-amber)" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Confirm Code Replacement</h3>
              </div>
            </div>
            <div className="modal-body">
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                Applying this fix will overwrite the current editor code with the proposed correction.
                Are you sure you want to proceed?
              </p>
              <div className="code-snippet-box" style={{ maxHeight: '180px' }}>
                {correctedCode}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowApplyModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleConfirmApply}>
                Confirm & Overwrite
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
