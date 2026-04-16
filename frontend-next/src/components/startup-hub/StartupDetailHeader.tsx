import VerificationBadge from '@/components/startup-hub/VerificationBadge';
import { formatStartupTimestamp, type StartupCompanyListItem, type StartupVerificationInfo } from '@/utils/startupHubApi';

type StartupDetailHeaderProps = {
  company: StartupCompanyListItem;
  verification: StartupVerificationInfo;
  description: string | null;
  lastUpdated: string | null;
};

const ENTITY_LABELS: Record<string, string> = {
  public_stock: 'Public Startup Stock',
  ipo_watch: 'IPO Watch',
  private_opportunity: 'Private Opportunity',
};

export default function StartupDetailHeader({
  company,
  verification,
  description,
  lastUpdated,
}: StartupDetailHeaderProps) {
  const quickFacts = [
    ENTITY_LABELS[company.entity_type] || 'Startup Entity',
    company.ticker,
    company.exchange,
    company.sector,
    company.status_label,
  ].filter(Boolean);

  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '24px',
        display: 'grid',
        gap: '18px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'grid', gap: '10px', maxWidth: '760px' }}>
          <div className="grid-label">Startup Stocks / Company Detail</div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'baseline', flexWrap: 'wrap' }}>
            <h1 style={{ fontSize: '34px', lineHeight: 1.05 }}>{company.company_name}</h1>
            {company.ticker ? (
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  color: 'var(--primary)',
                  fontSize: '14px',
                }}
              >
                {company.ticker}
              </span>
            ) : null}
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {quickFacts.map((fact) => (
              <span
                key={fact}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-elevated)',
                  padding: '6px 10px',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                }}
              >
                {fact}
              </span>
            ))}
          </div>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65 }}>
            {description || 'Deterministic company summary is not available yet.'}
          </p>
        </div>

        <div style={{ display: 'grid', gap: '12px', alignContent: 'start', minWidth: '220px' }}>
          <VerificationBadge level={company.verification_level} />
          <div
            style={{
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              padding: '14px',
              display: 'grid',
              gap: '6px',
            }}
          >
            <div className="grid-label">Rank Score</div>
            <div style={{ fontSize: '30px', fontWeight: 700 }}>{company.ranking.total_score.toFixed(1)}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
              {verification.description}
            </div>
          </div>
          <div
            style={{
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              padding: '14px',
              display: 'grid',
              gap: '4px',
            }}
          >
            <div className="grid-label">Last Updated</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              {formatStartupTimestamp(lastUpdated)}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
