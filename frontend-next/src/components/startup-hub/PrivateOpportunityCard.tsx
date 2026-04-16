import VerificationBadge from '@/components/startup-hub/VerificationBadge';
import type { StartupPrivateOpportunityItem } from '@/utils/startupHubApi';

type PrivateOpportunityCardProps = {
  company: StartupPrivateOpportunityItem;
};

function formatMoney(value: number | null): string {
  if (value == null || Number.isNaN(value)) {
    return 'Not disclosed';
  }
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

export default function PrivateOpportunityCard({ company }: PrivateOpportunityCardProps) {
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
            {[company.sector, company.stage].filter(Boolean).join(' · ') || 'Private research listing'}
          </div>
        </div>
        <VerificationBadge level={company.verification_level} />
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <span
          style={{
            border: '1px solid #FDE68A',
            background: '#FEF3C7',
            color: '#92400E',
            padding: '5px 8px',
            fontSize: '11px',
            fontWeight: 700,
          }}
        >
          {company.research_only_label}
        </span>
        <span
          style={{
            border: '1px solid var(--border)',
            background: 'var(--bg-elevated)',
            color: 'var(--text-secondary)',
            padding: '5px 8px',
            fontSize: '11px',
            fontWeight: 700,
          }}
        >
          {company.status_label || 'Source review pending'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '10px' }}>
        <div style={{ border: '1px solid var(--border)', padding: '12px', background: 'var(--bg-elevated)' }}>
          <div className="grid-label" style={{ marginBottom: '6px' }}>Rank Score</div>
          <div style={{ fontSize: '22px', fontWeight: 700 }}>{company.ranking.total_score.toFixed(1)}</div>
        </div>
        <div style={{ border: '1px solid var(--border)', padding: '12px', background: 'var(--bg-elevated)' }}>
          <div className="grid-label" style={{ marginBottom: '6px' }}>Valuation</div>
          <div style={{ fontSize: '16px', fontWeight: 700 }}>{formatMoney(company.valuation_usd)}</div>
        </div>
        <div style={{ border: '1px solid var(--border)', padding: '12px', background: 'var(--bg-elevated)' }}>
          <div className="grid-label" style={{ marginBottom: '6px' }}>Minimum</div>
          <div style={{ fontSize: '16px', fontWeight: 700 }}>{formatMoney(company.minimum_investment_usd)}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gap: '8px' }}>
        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
          <strong style={{ color: 'var(--foreground)' }}>Source:</strong>{' '}
          {company.source_name || 'Official source not stored yet'}
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
          <strong style={{ color: 'var(--foreground)' }}>Verification:</strong>{' '}
          {company.verification.description}
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
        {company.short_summary || company.risk_snippet || 'Private opportunity research summary is not available yet.'}
      </p>

      <div
        style={{
          border: '1px solid var(--border)',
          background: 'var(--bg-elevated)',
          padding: '12px',
          display: 'grid',
          gap: '6px',
        }}
      >
        <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{company.platform_availability_note}</div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{company.eligibility_note}</div>
      </div>

      {company.official_source_url ? (
        <a
          href={company.official_source_url}
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'inline-flex',
            justifySelf: 'start',
            padding: '10px 14px',
            border: '1px solid var(--border)',
            background: 'var(--bg-elevated)',
            color: 'var(--foreground)',
            textDecoration: 'none',
            fontWeight: 700,
          }}
        >
          Open Official Source
        </a>
      ) : (
        <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
          No official source link is stored for this research listing yet.
        </div>
      )}
    </article>
  );
}
