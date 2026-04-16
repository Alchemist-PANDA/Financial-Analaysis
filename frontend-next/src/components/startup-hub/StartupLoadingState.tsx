type StartupLoadingStateProps = {
  label?: string;
};

export default function StartupLoadingState({ label = 'Loading Startup Hub...' }: StartupLoadingStateProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '24px',
        display: 'grid',
        gap: '16px',
      }}
    >
      <div className="grid-label">{label}</div>
      <div style={{ display: 'grid', gap: '12px' }}>
        {[0, 1, 2].map((item) => (
          <div
            key={item}
            style={{
              height: '76px',
              border: '1px solid var(--border)',
              background: 'linear-gradient(90deg, #F8FAFC 0%, #EEF2FF 50%, #F8FAFC 100%)',
            }}
          />
        ))}
      </div>
    </section>
  );
}
