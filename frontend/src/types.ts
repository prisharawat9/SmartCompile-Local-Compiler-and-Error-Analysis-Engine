export interface Diagnostic {
  line: number;
  column: number;
  message: string;
  category: 'lexical' | 'syntax' | 'semantic' | 'runtime' | 'ai-assisted';
  severity: 'error' | 'warning' | 'info';
  code?: string | null;
}

export interface LocalFix {
  line: number;
  column: number;
  description: string;
  replacement: string;
  applied: boolean;
}

export interface TransparencyDetails {
  system_prompt: string;
  user_prompt: string;
  snippet_sent: string;
  line_start: number;
  line_end: number;
  full_file_char_count: number;
  snippet_char_count: number;
  prompt_tokens_est: number;
  bytes_saved_pct: number;
}

export interface TokensInfo {
  baseline_tokens: number;
  baseline_breakdown?: {
    full_file_tokens: number;
    baseline_input: number;
    baseline_output: number;
    baseline_total: number;
  };
  actual_input_tokens: number;
  actual_output_tokens: number;
  actual_total_tokens: number;
  is_mock: boolean;
  is_estimated: boolean;
  avoided_by_local: number;
  avoided_by_cache: number;
  avoided_by_snippet: number;
  total_tokens_saved: number;
  reduction_percentage: number;
  full_file_tokens_est: number;
  snippet_tokens_est: number;
}

export interface CacheDetails {
  cache_key: string;
  hit_count: number;
  created_at: string;
  reason: string;
}

export interface CompileResponse {
  status: 'passed_locally' | 'resolved_locally' | 'cache_hit' | 'ai_success' | 'ai_error';
  resolution_source: 'local' | 'cache' | 'ai' | 'mock';
  language: string;
  diagnostics: Diagnostic[];
  local_fixes: LocalFix[];
  corrected_code: string | null;
  explanation: string;
  suggested_fix?: string | null;
  ai_provider?: string | null;
  ai_model?: string | null;
  is_mock: boolean;
  tokens: TokensInfo;
  cache_hit: boolean;
  cache_details?: CacheDetails | null;
  request_transparency?: TransparencyDetails | null;
  error?: string | null;
}

export interface StatsResponse {
  total_compilations: number;
  resolutions: {
    local: number;
    cache: number;
    ai: number;
    mock: number;
  };
  real_ai: {
    calls: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  simulated_mock: {
    calls: number;
    simulated_input_tokens: number;
    simulated_output_tokens: number;
    total_simulated_tokens: number;
    note: string;
  };
  cache: {
    total_entries: number;
    total_hits: number;
    total_misses: number;
    total_lookups: number;
    hit_rate_percentage: number;
  };
  savings: {
    total_tokens_saved: number;
    baseline_tokens: number;
    percentage_reduction: number;
    baseline_definition: string;
  };
}

export interface HistoryItem {
  id: number;
  timestamp: string;
  language: string;
  status: string;
  resolution_source: string;
  ai_provider: string | null;
  ai_model: string | null;
  actual_input_tokens: number;
  actual_output_tokens: number;
  estimated_tokens_saved: number;
  baseline_tokens: number;
  explanation: string;
  corrected_code: string | null;
  source_preview: string;
  diagnostics: Diagnostic[];
  local_fixes: LocalFix[];
  request_transparency?: TransparencyDetails | null;
  error_message?: string | null;
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  active_ai_provider: string;
  active_model: string;
  api_key_configured: boolean;
  is_mock_provider: boolean;
  database_connected: boolean;
  compiler_engine_using_stub: boolean;
}
