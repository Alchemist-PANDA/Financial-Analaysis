type StartupThesisPanelProps = {
  thesisSummary: string | null;
  longSummary: string | null;
  strengths: string[];
};

export default function StartupThesisPanel({
  thesisSummary,
  longSummary,
  strengths,
}: StartupThesisPanelProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '20px',
        display: 'grid',
        gap: '16px',
      }}
    >
      <div className="grid-label">Startup Thesis</div>
      <div style={{ display: 'grid', gap: '10px' }}>
        <p style={{ color: 'var(--foreground)', lineHeight: 1.7 }}>
          {thesisSummary || 'Deterministic thesis summary is not available yet.'}
        </p>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          {longSummary || 'Detailed diagnosis is not available yet.'}
        </p>
      </div>

      <div style={{ display: 'grid', gap: '10px' }}>
        <div className="grid-label">Strengths</div>
        {strengths.length > 0 ? (
          strengths.map((strength) => (
            <div
              key={strength}
              style={{
                border: '1px solid #BBF7D0',
                background: '#F0FDF4',
                color: '#166534',
                padding: '12px',
                fontSize: '13px',
                lineHeight: 1.5,
              }}
            >
              {strength}
            </div>
          ))
        ) : (
          <div style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', padding: '12px', color: 'var(--text-secondary)', fontSize: '13px' }}>
            No strengths were extracted from the current deterministic payload.
          </div>
        )}
      </div>
    </section>
  );
}
