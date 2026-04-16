import Link from 'next/link';

type StartupEmptyStateProps = {
  title: string;
  message: string;
  actionHref?: string;
  actionLabel?: string;
};

export default function StartupEmptyState({
  title,
  message,
  actionHref,
  actionLabel,
}: StartupEmptyStateProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '24px',
        display: 'grid',
        gap: '12px',
        textAlign: 'center',
      }}
    >
      <h2 style={{ fontSize: '22px' }}>{title}</h2>
      <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', margin: '0 auto', lineHeight: 1.6 }}>
        {message}
      </p>
      {actionHref && actionLabel ? (
        <div>
          <Link
            href={actionHref}
            style={{
              display: 'inline-flex',
              padding: '10px 14px',
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              color: 'var(--foreground)',
              textDecoration: 'none',
              fontWeight: 600,
            }}
          >
            {actionLabel}
          </Link>
        </div>
      ) : null}
    </section>
  );
}
