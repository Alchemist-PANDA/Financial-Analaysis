type VerificationBadgeProps = {
  level: string;
};

const BADGE_META: Record<string, { label: string; background: string; color: string; border: string }> = {
  verified_public: {
    label: 'Verified Public',
    background: '#DCFCE7',
    color: '#166534',
    border: '#BBF7D0',
  },
  verified_ipo: {
    label: 'Verified IPO',
    background: '#DBEAFE',
    color: '#1D4ED8',
    border: '#BFDBFE',
  },
  source_verified_private: {
    label: 'Source Verified',
    background: '#E0F2FE',
    color: '#0369A1',
    border: '#BAE6FD',
  },
  partial: {
    label: 'Partial',
    background: '#FEF3C7',
    color: '#92400E',
    border: '#FDE68A',
  },
  unverified: {
    label: 'Unverified',
    background: '#E2E8F0',
    color: '#475569',
    border: '#CBD5E1',
  },
};

export default function VerificationBadge({ level }: VerificationBadgeProps) {
  const meta = BADGE_META[level] || BADGE_META.unverified;

  return (
    <span
      title={meta.label}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '5px 9px',
        border: `1px solid ${meta.border}`,
        background: meta.background,
        color: meta.color,
        fontSize: '11px',
        fontWeight: 700,
        letterSpacing: '0.03em',
        whiteSpace: 'nowrap',
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: '7px',
          height: '7px',
          borderRadius: '999px',
          background: meta.color,
          display: 'inline-block',
        }}
      />
      {meta.label}
    </span>
  );
}
