type StartupDisclaimerProps = {
  items: string[];
  lastUpdated?: string | null;
};

export default function StartupDisclaimer({ items, lastUpdated }: StartupDisclaimerProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '20px',
        display: 'grid',
        gap: '10px',
      }}
    >
      <div className="grid-label">Disclosures</div>
      {items.map((item) => (
        <div key={item} style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          {item}
        </div>
      ))}
      {lastUpdated ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '4px' }}>
          Last updated: {lastUpdated}
        </div>
      ) : null}
    </section>
  );
}
