import { getApiBaseUrl, getApiKey, safeFetch } from '@/utils/api';

export type StartupRankingBreakdown = {
  total_score: number;
  growth_score: number;
  quality_score: number;
  risk_score: number;
  verification_score: number;
  momentum_score: number;
  top_drivers: string[];
  red_flags: string[];
  explanation: string | null;
  verification_level?: string;
};

export type StartupVerificationInfo = {
  level: string;
  label: string;
  tone: string;
  description: string;
  is_verified: boolean;
  checks: Record<string, boolean>;
  sources_considered: number;
  missing_checks: string[];
};

export type StartupCacheStatus = {
  key: string;
  source: string;
  ttl_seconds: number;
  age_seconds: number;
  is_stale: boolean;
};

export type StartupResponseState = {
  stale: boolean;
  stale_message: string | null;
  cache_status: StartupCacheStatus | null;
};

export type StartupSourceItem = {
  source_name: string;
  source_type: string;
  source_url: string | null;
  is_official: boolean;
  verification_level: string;
  published_at: string | null;
  last_checked_at: string | null;
  notes: string | null;
};

export type StartupMetricItem = {
  key: string;
  label: string;
  value: unknown;
  formatted_value: string;
  context: string | null;
};

export type StartupCompanyListItem = {
  slug: string;
  company_name: string;
  entity_type: string;
  sector: string | null;
  ticker: string | null;
  exchange: string | null;
  stage: string | null;
  status_label: string | null;
  short_summary: string | null;
  verification_level: string;
  ranking: StartupRankingBreakdown;
  source_count: number;
  data_completeness_score: number;
  research_only: boolean;
  last_updated: string | null;
};

export type StartupIpoListItem = StartupCompanyListItem & {
  filing_status: string | null;
  proposed_exchange: string | null;
  expected_window: string | null;
  filing_freshness_label: string | null;
  official_source_url: string | null;
  source_name: string | null;
  source_is_official: boolean;
  risk_snippet: string | null;
};

export type StartupPrivateOpportunityItem = StartupCompanyListItem & {
  valuation_usd: number | null;
  minimum_investment_usd: number | null;
  official_source_url: string | null;
  source_name: string | null;
  source_is_official: boolean;
  verification: StartupVerificationInfo;
  research_only_label: string;
  platform_availability_note: string;
  eligibility_note: string;
  risk_snippet: string | null;
};

export type StartupCompanyDetailResponse = StartupResponseState & {
  feature: string;
  status: string;
  enabled: boolean;
  disclaimer: string[];
  company: StartupCompanyListItem;
  verification: StartupVerificationInfo;
  thesis_summary: string | null;
  long_summary: string | null;
  description: string | null;
  strengths: string[];
  risks: string[];
  metrics: Record<string, unknown>;
  metric_highlights: StartupMetricItem[];
  snapshot: Record<string, unknown>;
  sources: StartupSourceItem[];
  last_updated: string | null;
};

export type StartupAgentQueryRequest = {
  query: string;
  entity_type?: string | null;
  limit?: number;
  include_explanations?: boolean;
};

export type StartupAgentQueryResponse = StartupResponseState & {
  feature: string;
  status: string;
  enabled: boolean;
  disclaimer: string[];
  query: string;
  mode: string;
  interpreted_filters: Record<string, unknown>;
  summary: string;
  reasoning_points: string[];
  comparison: Record<string, unknown>;
  matches: StartupCompanyListItem[];
  confidence_level: string;
  last_updated: string | null;
};

export type StartupCompareResponse = StartupResponseState & {
  feature: string;
  status: string;
  enabled: boolean;
  disclaimer: string[];
  left: StartupCompanyListItem;
  right: StartupCompanyListItem;
  left_summary: string | null;
  right_summary: string | null;
  category_winners: Record<string, string>;
  overall_summary: string;
  ai_explanation: string | null;
  comparison_notes: string[];
  last_updated: string | null;
};

export type StartupHubHomeResponse = StartupResponseState & {
  feature: string;
  status: string;
  enabled: boolean;
  disclaimer: string[];
  featured: StartupCompanyListItem[];
  public_companies: StartupCompanyListItem[];
  ipo_preview: StartupCompanyListItem[];
  private_preview: StartupCompanyListItem[];
  counts: Record<string, number>;
  last_updated: string | null;
};

export type StartupCompaniesResponse = StartupResponseState & {
  feature: string;
  status: string;
  enabled: boolean;
  disclaimer: string[];
  filters: Record<string, string | null>;
  items: StartupCompanyListItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
  };
  last_updated: string | null;
};

export type StartupIposResponse = StartupResponseState & {
  feature: string;
  status: string;
  enabled: boolean;
  disclaimer: string[];
  items: StartupIpoListItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
  };
  last_updated: string | null;
};

export type StartupPrivateResponse = StartupResponseState & {
  feature: string;
  status: string;
  enabled: boolean;
  disclaimer: string[];
  items: StartupPrivateOpportunityItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
  };
  last_updated: string | null;
};

const BASE_URL = getApiBaseUrl();
const API_KEY = getApiKey();

async function requestStartupHub<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await safeFetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'X-API-Key': API_KEY,
      ...(options?.headers || {}),
    },
  });

  if (!response.success) {
    throw new Error(response.error || 'Startup Hub request failed.');
  }

  return response.data as T;
}

export async function fetchStartupHubHome(): Promise<StartupHubHomeResponse> {
  return requestStartupHub<StartupHubHomeResponse>('/api/startup-hub/home');
}

export async function fetchStartupCompanies(params?: {
  entityType?: string;
  search?: string;
}): Promise<StartupCompaniesResponse> {
  const query = new URLSearchParams();
  if (params?.entityType) {
    query.set('entity_type', params.entityType);
  }
  if (params?.search) {
    query.set('search', params.search);
  }
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return requestStartupHub<StartupCompaniesResponse>(`/api/startup-hub/companies${suffix}`);
}

export async function fetchStartupCompanyDetail(slug: string): Promise<StartupCompanyDetailResponse> {
  return requestStartupHub<StartupCompanyDetailResponse>(`/api/startup-hub/company/${encodeURIComponent(slug)}`);
}

export async function fetchStartupIpos(): Promise<StartupIposResponse> {
  return requestStartupHub<StartupIposResponse>('/api/startup-hub/ipos');
}

export async function fetchStartupPrivateOpportunities(): Promise<StartupPrivateResponse> {
  return requestStartupHub<StartupPrivateResponse>('/api/startup-hub/private');
}

export async function submitStartupAgentQuery(
  payload: StartupAgentQueryRequest
): Promise<StartupAgentQueryResponse> {
  return requestStartupHub<StartupAgentQueryResponse>('/api/startup-hub/agent/query', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchStartupComparison(
  leftSlug: string,
  rightSlug: string
): Promise<StartupCompareResponse> {
  const query = new URLSearchParams({
    left: leftSlug,
    right: rightSlug,
  });
  return requestStartupHub<StartupCompareResponse>(`/api/startup-hub/compare?${query.toString()}`);
}

export function formatStartupTimestamp(value: string | null): string {
  if (!value) {
    return 'Not updated yet';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return 'Unknown update time';
  }

  return parsed.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}
