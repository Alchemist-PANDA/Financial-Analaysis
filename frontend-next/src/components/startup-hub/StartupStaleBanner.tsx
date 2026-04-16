import type { StartupCacheStatus } from '@/utils/startupHubApi';

type StartupStaleBannerProps = {
  message?: string | null;
  cacheStatus?: StartupCacheStatus | null;
};

export default function StartupStaleBanner({ message, cacheStatus }: StartupStaleBannerProps) {
  const detail =
    message ||
    (cacheStatus?.source === 'stale_cache_fallback'
      ? 'A stale cached response is being shown because a fresh refresh was unavailable.'
      : 'This data is being served from a cache and may be out of date.');

  return (
    <section
      style={{
        border: '1px solid #FDE68A',
        background: 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)',
        color: '#78350F',
        boxShadow: 'var(--shadow-card)',
        padding: '16px 18px',
        display: 'grid',
        gap: '6px',
      }}
    >
      <div className="grid-label" style={{ color: '#92400E', fontSize: '11px', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
        Stale Data Notice
      </div>
      <div style={{ lineHeight: 1.5, fontSize: '14px' }}>{detail}</div>
      {cacheStatus ? (
        <div style={{ fontSize: '12px', color: '#92400E', opacity: 0.8 }}>
          Cache source: <span style={{ fontWeight: 700 }}>{cacheStatus.source.replaceAll('_', ' ')}</span> · 
          Cache age: <span style={{ fontWeight: 700 }}>{Math.round(cacheStatus.age_seconds)}s</span>
        </div>
      ) : null}
    </section>
  );
}
