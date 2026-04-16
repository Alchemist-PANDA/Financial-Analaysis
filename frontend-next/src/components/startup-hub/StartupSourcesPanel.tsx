import type { StartupSourceItem } from '@/utils/startupHubApi';

type StartupSourcesPanelProps = {
  sources: StartupSourceItem[];
};

export default function StartupSourcesPanel({ sources }: StartupSourcesPanelProps) {
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
      <div className="grid-label">Sources</div>
      {sources.length > 0 ? (
        <div style={{ display: 'grid', gap: '10px' }}>
          {sources.map((source) => (
            <article
              key={`${source.source_name}-${source.source_url || source.source_type}`}
              style={{
                border: '1px solid var(--border)',
                background: 'var(--bg-elevated)',
                padding: '14px',
                display: 'grid',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'start', flexWrap: 'wrap' }}>
                <div style={{ display: 'grid', gap: '4px' }}>
                  <div style={{ fontSize: '16px', fontWeight: 700 }}>{source.source_name}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{source.source_type}</div>
                </div>
                <div
                  style={{
                    border: `1px solid ${source.is_official ? '#BBF7D0' : 'var(--border)'}`,
                    background: source.is_official ? '#F0FDF4' : 'var(--bg-surface)',
                    color: source.is_official ? '#166534' : 'var(--text-secondary)',
                    padding: '4px 8px',
                    fontSize: '11px',
                    fontWeight: 700,
                  }}
                >
                  {source.is_official ? 'Official Source' : 'Reference Source'}
                </div>
              </div>
              {source.notes ? (
                <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>{source.notes}</div>
              ) : null}
              {source.source_url ? (
                <a
                  href={source.source_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 700, fontSize: '13px' }}
                >
                  Open source link
                </a>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>No direct source URL stored.</div>
              )}
            </article>
          ))}
        </div>
      ) : (
        <div style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', padding: '12px', color: 'var(--text-secondary)', fontSize: '13px' }}>
          No source records are stored for this company yet.
        </div>
      )}
    </section>
  );
}
