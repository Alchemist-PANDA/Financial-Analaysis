import Link from 'next/link';

import VerificationBadge from '@/components/startup-hub/VerificationBadge';
import type { StartupCompanyListItem } from '@/utils/startupHubApi';

type StartupTableProps = {
  companies: StartupCompanyListItem[];
};

export default function StartupTable({ companies }: StartupTableProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        overflowX: 'auto',
      }}
    >
      <table className="terminal-table">
        <thead>
          <tr>
            <th>Company</th>
            <th>Sector</th>
            <th>Score</th>
            <th>Verification</th>
            <th>Summary</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {companies.map((company) => (
            <tr key={company.slug}>
              <td>
                <div style={{ fontWeight: 700 }}>{company.company_name}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                  {[company.ticker, company.exchange].filter(Boolean).join(' · ')}
                </div>
              </td>
              <td>{company.sector || '--'}</td>
              <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{company.ranking.total_score.toFixed(1)}</td>
              <td>
                <VerificationBadge level={company.verification_level} />
              </td>
              <td style={{ minWidth: '280px', color: 'var(--text-secondary)' }}>
                {company.short_summary || 'No deterministic summary available yet.'}
              </td>
              <td>
                <Link
                  href={`/startup-hub/company/${company.slug}`}
                  style={{
                    color: 'var(--primary)',
                    textDecoration: 'none',
                    fontWeight: 700,
                  }}
                >
                  Detail
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
