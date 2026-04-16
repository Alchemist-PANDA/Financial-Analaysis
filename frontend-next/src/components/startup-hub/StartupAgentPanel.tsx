import Link from 'next/link';

import VerificationBadge from '@/components/startup-hub/VerificationBadge';
import StartupStaleBanner from '@/components/startup-hub/StartupStaleBanner';
import type { StartupAgentQueryResponse } from '@/utils/startupHubApi';

type StartupAgentPanelProps = {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmit: () => void;
  onPromptSelect: (value: string) => void;
  isLoading: boolean;
  error: string | null;
  response: StartupAgentQueryResponse | null;
  promptSuggestions: string[];
};

export default function StartupAgentPanel({
  query,
  onQueryChange,
  onSubmit,
  onPromptSelect,
  isLoading,
  error,
  response,
  promptSuggestions,
}: StartupAgentPanelProps) {
  const comparisonSummary = typeof response?.comparison?.summary === 'string' ? response.comparison.summary : null;
  const comparisonWinners =
    response?.comparison && typeof response.comparison.category_winners === 'object'
      ? Object.entries(response.comparison.category_winners as Record<string, string>)
      : [];

  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '20px',
        display: 'grid',
        gap: '16px',
      }}
    >
      <div style={{ display: 'grid', gap: '6px' }}>
        <div className="grid-label">Startup Research Assistant</div>
        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          Deterministic query layer over Startup Hub scores, verification data, and source metadata. It does not invent missing metrics or provide personalized advice.
        </div>
      </div>

      <div style={{ display: 'grid', gap: '10px' }}>
        <textarea
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Ask for a deterministic screen, compare, or explanation..."
          rows={3}
          style={{
            width: '100%',
            border: '1px solid var(--border)',
            background: 'var(--bg-elevated)',
            color: 'var(--foreground)',
            padding: '12px 14px',
            resize: 'vertical',
            font: 'inherit',
            lineHeight: 1.5,
          }}
        />
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {promptSuggestions.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => onPromptSelect(prompt)}
              style={{
                border: '1px solid var(--border)',
                background: 'var(--bg-elevated)',
                color: 'var(--foreground)',
                padding: '8px 10px',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              {prompt}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
            Supports compare, explain-top, lower-risk screens, and IPO/private summaries.
          </div>
          <button
            type="button"
            onClick={onSubmit}
            disabled={isLoading || !query.trim()}
            style={{
              border: '1px solid var(--border)',
              background: isLoading || !query.trim() ? 'var(--bg-elevated)' : '#EFF6FF',
              color: isLoading || !query.trim() ? 'var(--text-secondary)' : 'var(--primary)',
              padding: '10px 14px',
              fontWeight: 700,
              cursor: isLoading || !query.trim() ? 'default' : 'pointer',
            }}
          >
            {isLoading ? 'Running Query...' : 'Run Research Query'}
          </button>
        </div>
      </div>

      {error ? (
        <div
          style={{
            border: '1px solid #FECACA',
            background: '#FEF2F2',
            color: '#991B1B',
            padding: '12px',
            fontSize: '13px',
          }}
        >
          {error}
        </div>
      ) : null}

      {response?.stale ? (
        <StartupStaleBanner message={response.stale_message} cacheStatus={response.cache_status} />
      ) : null}

      {response ? (
        <div style={{ display: 'grid', gap: '14px' }}>
          <div
            style={{
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              padding: '14px',
              display: 'grid',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
              <div className="grid-label">Assistant Output</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                Confidence: {response.confidence_level}
              </div>
            </div>
            <div style={{ color: 'var(--foreground)', lineHeight: 1.7 }}>{response.summary}</div>
            {response.reasoning_points.length > 0 ? (
              <div style={{ display: 'grid', gap: '8px' }}>
                {response.reasoning_points.map((point) => (
                  <div
                    key={point}
                    style={{
                      border: '1px solid var(--border)',
                      background: 'var(--bg-surface)',
                      padding: '10px 12px',
                      color: 'var(--text-secondary)',
                      fontSize: '13px',
                    }}
                  >
                    {point}
                  </div>
                ))}
              </div>
            ) : null}
            {comparisonSummary ? (
              <div style={{ display: 'grid', gap: '8px' }}>
                <div className="grid-label">Comparison</div>
                <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{comparisonSummary}</div>
                {comparisonWinners.length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '8px' }}>
                    {comparisonWinners.map(([category, winner]) => (
                      <div
                        key={category}
                        style={{
                          border: '1px solid var(--border)',
                          background: 'var(--bg-surface)',
                          padding: '10px',
                          display: 'grid',
                          gap: '4px',
                        }}
                      >
                        <div className="grid-label">{category}</div>
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{winner}</div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>

          {response.matches.length > 0 ? (
            <div style={{ display: 'grid', gap: '10px' }}>
              <div className="grid-label">Matched Companies</div>
              {response.matches.map((company) => (
                <div
                  key={company.slug}
                  style={{
                    border: '1px solid var(--border)',
                    background: 'var(--bg-elevated)',
                    padding: '14px',
                    display: 'grid',
                    gap: '10px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'start', flexWrap: 'wrap' }}>
                    <div style={{ display: 'grid', gap: '4px' }}>
                      <div style={{ fontSize: '18px', fontWeight: 700 }}>{company.company_name}</div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                        {[company.ticker, company.sector, company.status_label].filter(Boolean).join(' · ')}
                      </div>
                    </div>
                    <div style={{ display: 'grid', gap: '8px', justifyItems: 'end' }}>
                      <VerificationBadge level={company.verification_level} />
                      <div style={{ fontSize: '18px', fontWeight: 700 }}>{company.ranking.total_score.toFixed(1)}</div>
                    </div>
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
                    {company.short_summary || company.ranking.explanation || 'No deterministic summary available.'}
                  </div>
                  {company.entity_type === 'public_stock' ? (
                    <Link
                      href={`/startup-hub/company/${company.slug}`}
                      style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 700, fontSize: '13px' }}
                    >
                      Open company detail
                    </Link>
                  ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      Detail route is not implemented for this entity type yet.
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : null}

          <div
            style={{
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              padding: '12px',
              display: 'grid',
              gap: '6px',
            }}
          >
            {response.disclaimer.map((item) => (
              <div key={item} style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                {item}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
