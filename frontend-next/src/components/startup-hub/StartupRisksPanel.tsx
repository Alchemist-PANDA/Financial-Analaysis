type StartupRisksPanelProps = {
  risks: string[];
};

export default function StartupRisksPanel({ risks }: StartupRisksPanelProps) {
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
      <div className="grid-label">Risks</div>
      {risks.length > 0 ? (
        risks.map((risk) => (
          <div
            key={risk}
            style={{
              border: '1px solid #FECACA',
              background: '#FEF2F2',
              color: '#991B1B',
              padding: '12px',
              fontSize: '13px',
              lineHeight: 1.55,
            }}
          >
            {risk}
          </div>
        ))
      ) : (
        <div style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', padding: '12px', color: 'var(--text-secondary)', fontSize: '13px' }}>
          No explicit deterministic risks were extracted from the current payload.
        </div>
      )}
    </section>
  );
}
