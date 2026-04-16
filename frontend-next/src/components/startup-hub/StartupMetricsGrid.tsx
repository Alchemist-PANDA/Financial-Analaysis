import type { StartupMetricItem } from '@/utils/startupHubApi';

type StartupMetricsGridProps = {
  metrics: StartupMetricItem[];
};

export default function StartupMetricsGrid({ metrics }: StartupMetricsGridProps) {
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
      <div className="grid-label">Financial Metrics</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '10px' }}>
        {metrics.map((metric) => (
          <div
            key={metric.key}
            style={{
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              padding: '14px',
              display: 'grid',
              gap: '8px',
            }}
          >
            <div className="grid-label">{metric.label}</div>
            <div style={{ fontSize: '24px', fontWeight: 700 }}>{metric.formatted_value}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: 1.5 }}>
              {metric.context || 'Metric context unavailable.'}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
