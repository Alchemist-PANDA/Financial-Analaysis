import Link from 'next/link';

type StartupHubShellProps = {
  title: string;
  description: string;
  section: string;
  enabled?: boolean;
  slug?: string;
};

const NAV_ITEMS = [
  { label: 'Startup Hub', href: '/startup-hub' },
  { label: 'Startup Stocks', href: '/startup-hub/stocks' },
  { label: 'IPO Watch', href: '/startup-hub/ipos' },
  { label: 'Private Opportunities', href: '/startup-hub/private' },
];

const DISCLAIMER_ITEMS = [
  'Research only',
  'Not investment advice',
  'Verify with official sources',
];

export default function StartupHubShell({
  title,
  description,
  section,
  enabled = false,
  slug,
}: StartupHubShellProps) {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: 'var(--background)',
        color: 'var(--foreground)',
        padding: '40px 24px',
      }}
    >
      <div style={{ maxWidth: '980px', margin: '0 auto', display: 'grid', gap: '20px' }}>
        <header
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            boxShadow: 'var(--shadow-card)',
            padding: '24px',
            display: 'grid',
            gap: '12px',
          }}
        >
          <div className="grid-label">{section}</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ display: 'grid', gap: '8px' }}>
              <h1 style={{ fontSize: '32px', lineHeight: 1.1 }}>{title}</h1>
              <p style={{ maxWidth: '700px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{description}</p>
              {slug ? (
                <div className="grid-value" style={{ color: 'var(--text-secondary)' }}>
                  Slug: {slug}
                </div>
              ) : null}
            </div>
            <div
              style={{
                alignSelf: 'start',
                border: '1px solid var(--border)',
                padding: '10px 12px',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                background: enabled ? '#DCFCE7' : '#FEF3C7',
                color: enabled ? '#166534' : '#92400E',
              }}
            >
              {enabled ? 'Feature flag on' : 'Feature flag off'}
            </div>
          </div>
        </header>

        <section
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            padding: '24px',
            display: 'grid',
            gap: '16px',
          }}
        >
          <div className="grid-label">Navigation</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  border: '1px solid var(--border)',
                  background: 'var(--bg-elevated)',
                  padding: '10px 14px',
                  color: 'var(--foreground)',
                  textDecoration: 'none',
                  fontWeight: 600,
                }}
              >
                {item.label}
              </Link>
            ))}
            <Link
              href="/"
              style={{
                border: '1px solid var(--border)',
                background: 'transparent',
                padding: '10px 14px',
                color: 'var(--text-secondary)',
                textDecoration: 'none',
                fontWeight: 600,
              }}
            >
              Back To Terminal
            </Link>
          </div>
        </section>

        <section
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            padding: '24px',
            display: 'grid',
            gap: '12px',
          }}
        >
          <div className="grid-label">Placeholder Status</div>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            This route is scaffolded for Startup Hub Phase 1 only. API wiring and production UI are intentionally not
            implemented yet.
          </p>
        </section>

        <section
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            padding: '24px',
            display: 'grid',
            gap: '8px',
          }}
        >
          <div className="grid-label">Disclosures</div>
          {DISCLAIMER_ITEMS.map((item) => (
            <div key={item} style={{ color: 'var(--text-secondary)' }}>
              {item}
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}
