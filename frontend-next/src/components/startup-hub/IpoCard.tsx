import VerificationBadge from '@/components/startup-hub/VerificationBadge';
import { formatStartupTimestamp, type StartupIpoListItem } from '@/utils/startupHubApi';

type IpoCardProps = {
  company: StartupIpoListItem;
};

export default function IpoCard({ company }: IpoCardProps) {
  return (
    <article
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '20px',
        display: 'grid',
        gap: '14px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: '6px' }}>
          <h3 style={{ fontSize: '22px', lineHeight: 1.1 }}>{company.company_name}</h3>
          <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            {[company.sector, company.proposed_exchange || company.exchange].filter(Boolean).join(' · ') || 'IPO watch entry'}
          </div>
        </div>
        <VerificationBadge level={company.verification_level} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '10px' }}>
        <div style={{ border: '1px solid var(--border)', padding: '12px', background: 'var(--bg-elevated)' }}>
          <div className="grid-label" style={{ marginBottom: '6px' }}>Rank Score</div>
          <div style={{ fontSize: '22px', fontWeight: 700 }}>{company.ranking.total_score.toFixed(1)}</div>
        </div>
        <div style={{ border: '1px solid var(--border)', padding: '12px', background: 'var(--bg-elevated)' }}>
          <div className="grid-label" style={{ marginBottom: '6px' }}>Completeness</div>
          <div style={{ fontSize: '22px', fontWeight: 700 }}>{Math.round(company.data_completeness_score * 100)}%</div>
        </div>
        <div style={{ border: '1px solid var(--border)', padding: '12px', background: 'var(--bg-elevated)' }}>
          <div className="grid-label" style={{ marginBottom: '6px' }}>Sources</div>
          <div style={{ fontSize: '22px', fontWeight: 700 }}>{company.source_count}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gap: '8px' }}>
        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
          <strong style={{ color: 'var(--foreground)' }}>Filing status:</strong>{' '}
          {company.filing_status || company.status_label || 'Not confirmed'}
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
          <strong style={{ color: 'var(--foreground)' }}>Expected window:</strong>{' '}
          {company.expected_window || company.filing_freshness_label || formatStartupTimestamp(company.last_updated)}
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
        {company.risk_snippet || company.short_summary || 'Incomplete IPO data is acceptable here, but it should be verified against official filings.'}
      </p>

      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
          {company.source_name
            ? `${company.source_is_official ? 'Official' : 'Reference'} source: ${company.source_name}`
            : 'No official source link stored yet'}
        </div>
        {company.official_source_url ? (
          <a
            href={company.official_source_url}
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'inline-flex',
              padding: '10px 14px',
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              color: 'var(--foreground)',
              textDecoration: 'none',
              fontWeight: 700,
            }}
          >
            Open Source
          </a>
        ) : null}
      </div>
    </article>
  );
}
