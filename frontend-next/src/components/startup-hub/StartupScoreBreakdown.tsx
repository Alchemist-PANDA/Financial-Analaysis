import type { StartupRankingBreakdown } from '@/utils/startupHubApi';

type StartupScoreBreakdownProps = {
  ranking: StartupRankingBreakdown;
};

const SCORE_ITEMS: Array<{ key: keyof StartupRankingBreakdown; label: string }> = [
  { key: 'growth_score', label: 'Growth' },
  { key: 'quality_score', label: 'Quality' },
  { key: 'risk_score', label: 'Risk Control' },
  { key: 'verification_score', label: 'Verification' },
  { key: 'momentum_score', label: 'Momentum' },
];

export default function StartupScoreBreakdown({ ranking }: StartupScoreBreakdownProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '20px',
        display: 'grid',
        gap: '18px',
      }}
    >
      <div style={{ display: 'grid', gap: '8px' }}>
        <div className="grid-label">Score Breakdown</div>
        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          {ranking.explanation || 'Deterministic ranking explanation is not available yet.'}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
        <div
          style={{
            border: '1px solid var(--border)',
            background: 'var(--bg-elevated)',
            padding: '14px',
            display: 'grid',
            gap: '6px',
          }}
        >
          <div className="grid-label">Total</div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{ranking.total_score.toFixed(1)}</div>
        </div>
        {SCORE_ITEMS.map((item) => (
          <div
            key={item.key}
            style={{
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              padding: '14px',
              display: 'grid',
              gap: '6px',
            }}
          >
            <div className="grid-label">{item.label}</div>
            <div style={{ fontSize: '24px', fontWeight: 700 }}>{Number(ranking[item.key]).toFixed(1)}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
        <div style={{ display: 'grid', gap: '10px' }}>
          <div className="grid-label">Top Drivers</div>
          {ranking.top_drivers.length > 0 ? (
            ranking.top_drivers.map((driver) => (
              <div
                key={driver}
                style={{
                  border: '1px solid #BBF7D0',
                  background: '#F0FDF4',
                  color: '#166534',
                  padding: '12px',
                  fontSize: '13px',
                  lineHeight: 1.5,
                }}
              >
                {driver}
              </div>
            ))
          ) : (
            <div style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', padding: '12px', color: 'var(--text-secondary)', fontSize: '13px' }}>
              No positive drivers were extracted from the current deterministic ranking payload.
            </div>
          )}
        </div>

        <div style={{ display: 'grid', gap: '10px' }}>
          <div className="grid-label">Red Flags</div>
          {ranking.red_flags.length > 0 ? (
            ranking.red_flags.map((flag) => (
              <div
                key={flag}
                style={{
                  border: '1px solid #FECACA',
                  background: '#FEF2F2',
                  color: '#991B1B',
                  padding: '12px',
                  fontSize: '13px',
                  lineHeight: 1.5,
                }}
              >
                {flag}
              </div>
            ))
          ) : (
            <div style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', padding: '12px', color: 'var(--text-secondary)', fontSize: '13px' }}>
              No major red flags were extracted from the current deterministic ranking payload.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
