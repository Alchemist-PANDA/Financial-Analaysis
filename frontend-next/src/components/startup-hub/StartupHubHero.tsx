import Link from 'next/link';

type StartupHubHeroProps = {
  title: string;
  description: string;
  companyCount: number;
  topCompanyName?: string;
  topCompanyScore?: number;
  lastUpdated?: string;
};

export default function StartupHubHero({
  title,
  description,
  companyCount,
  topCompanyName,
  topCompanyScore,
  lastUpdated,
}: StartupHubHeroProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '28px',
        display: 'grid',
        gap: '20px',
      }}
    >
      <div style={{ display: 'grid', gap: '10px' }}>
        <div className="grid-label">Startup Hub</div>
        <h1 style={{ fontSize: '34px', lineHeight: 1.05, maxWidth: '720px' }}>{title}</h1>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, maxWidth: '760px' }}>{description}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
        <div style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', padding: '16px' }}>
          <div className="grid-label" style={{ marginBottom: '8px' }}>Tracked Public Startups</div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{companyCount}</div>
        </div>
        <div style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', padding: '16px' }}>
          <div className="grid-label" style={{ marginBottom: '8px' }}>Top Ranked</div>
          <div style={{ fontSize: '18px', fontWeight: 700 }}>{topCompanyName || 'No ranking yet'}</div>
          <div style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
            {typeof topCompanyScore === 'number' ? `${topCompanyScore.toFixed(1)} / 100` : 'Waiting for score'}
          </div>
        </div>
        <div style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', padding: '16px' }}>
          <div className="grid-label" style={{ marginBottom: '8px' }}>Platform Use</div>
          <div style={{ fontSize: '18px', fontWeight: 700 }}>Research Only</div>
          <div style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>{lastUpdated || 'Update time unavailable'}</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <Link
          href="/startup-hub/stocks"
          style={{
            display: 'inline-flex',
            padding: '11px 16px',
            border: '1px solid var(--border-active)',
            background: '#EFF6FF',
            color: 'var(--primary)',
            textDecoration: 'none',
            fontWeight: 700,
          }}
        >
          Browse Startup Stocks
        </Link>
        <Link
          href="/"
          style={{
            display: 'inline-flex',
            padding: '11px 16px',
            border: '1px solid var(--border)',
            background: 'transparent',
            color: 'var(--foreground)',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          Back To Terminal
        </Link>
      </div>
    </section>
  );
}
