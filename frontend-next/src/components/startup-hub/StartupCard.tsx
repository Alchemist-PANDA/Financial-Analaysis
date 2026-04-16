import Link from 'next/link';

import VerificationBadge from '@/components/startup-hub/VerificationBadge';
import type { StartupCompanyListItem } from '@/utils/startupHubApi';

type StartupCardProps = {
  company: StartupCompanyListItem;
};

export default function StartupCard({ company }: StartupCardProps) {
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
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <h3 style={{ fontSize: '22px', lineHeight: 1.1 }}>{company.company_name}</h3>
            {company.ticker ? (
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--primary)',
                  fontWeight: 700,
                  fontSize: '13px',
                }}
              >
                {company.ticker}
              </span>
            ) : null}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            {[company.sector, company.exchange].filter(Boolean).join(' · ') || 'Public startup stock'}
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
          <div className="grid-label" style={{ marginBottom: '6px' }}>Sources</div>
          <div style={{ fontSize: '22px', fontWeight: 700 }}>{company.source_count}</div>
        </div>
        <div style={{ border: '1px solid var(--border)', padding: '12px', background: 'var(--bg-elevated)' }}>
          <div className="grid-label" style={{ marginBottom: '6px' }}>Completeness</div>
          <div style={{ fontSize: '22px', fontWeight: 700 }}>{Math.round(company.data_completeness_score * 100)}%</div>
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
        {company.short_summary || 'No deterministic summary available yet.'}
      </p>

      {company.ranking.top_drivers.length > 0 ? (
        <div style={{ display: 'grid', gap: '6px' }}>
          <div className="grid-label">Top Drivers</div>
          {company.ranking.top_drivers.map((driver) => (
            <div key={driver} style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              {driver}
            </div>
          ))}
        </div>
      ) : null}

      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
          {company.research_only ? 'Research only' : 'Review source terms'}
        </div>
        <Link
          href={`/startup-hub/company/${company.slug}`}
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
          View Detail
        </Link>
      </div>
    </article>
  );
}
