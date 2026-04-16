import Link from 'next/link';

import VerificationBadge from '@/components/startup-hub/VerificationBadge';
import type { StartupCompanyListItem } from '@/utils/startupHubApi';

type StartupRankingListProps = {
  companies: StartupCompanyListItem[];
  title?: string;
};

export default function StartupRankingList({
  companies,
  title = 'Top Ranked Public Startups',
}: StartupRankingListProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '20px',
        display: 'grid',
        gap: '14px',
      }}
    >
      <div className="grid-label">{title}</div>
      <div style={{ display: 'grid', gap: '10px' }}>
        {companies.map((company, index) => (
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
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'start' }}>
              <div style={{ display: 'grid', gap: '4px' }}>
                <div className="grid-label">Rank #{index + 1}</div>
                <div style={{ fontSize: '18px', fontWeight: 700 }}>{company.company_name}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                  {[company.ticker, company.sector].filter(Boolean).join(' · ')}
                </div>
              </div>
              <div style={{ display: 'grid', gap: '8px', justifyItems: 'end' }}>
                <div style={{ fontSize: '20px', fontWeight: 700 }}>{company.ranking.total_score.toFixed(1)}</div>
                <VerificationBadge level={company.verification_level} />
              </div>
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
              {company.ranking.explanation || company.short_summary || 'No explanation available.'}
            </div>
            <Link
              href={`/startup-hub/company/${company.slug}`}
              style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 700, fontSize: '13px' }}
            >
              Open company detail
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}
