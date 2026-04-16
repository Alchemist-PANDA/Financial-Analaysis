import Link from 'next/link';

import VerificationBadge from '@/components/startup-hub/VerificationBadge';
import StartupStaleBanner from '@/components/startup-hub/StartupStaleBanner';
import type { StartupCompanyListItem, StartupCompareResponse } from '@/utils/startupHubApi';

type StartupComparisonPanelProps = {
  companies: StartupCompanyListItem[];
  selectedLeftSlug: string;
  selectedRightSlug: string;
  onLeftChange: (value: string) => void;
  onRightChange: (value: string) => void;
  onCompare: () => void;
  isLoading: boolean;
  error: string | null;
  response: StartupCompareResponse | null;
  fixedLeftCompany?: StartupCompanyListItem | null;
};

function SelectField({
  label,
  value,
  onChange,
  companies,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  companies: StartupCompanyListItem[];
  disabled?: boolean;
}) {
  return (
    <label style={{ display: 'grid', gap: '6px' }}>
      <span className="grid-label">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        style={{
          border: '1px solid var(--border)',
          background: 'var(--bg-elevated)',
          color: 'var(--foreground)',
          padding: '10px 12px',
          minWidth: '220px',
        }}
      >
        <option value="">Select company</option>
        {companies.map((company) => (
          <option key={company.slug} value={company.slug}>
            {company.company_name}
          </option>
        ))}
      </select>
    </label>
  );
}

function CompanySummary({ company, summary }: { company: StartupCompanyListItem; summary: string | null }) {
  return (
    <article
      style={{
        border: '1px solid var(--border)',
        background: 'var(--bg-elevated)',
        padding: '16px',
        display: 'grid',
        gap: '10px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: '4px' }}>
          <div style={{ fontSize: '18px', fontWeight: 700 }}>{company.company_name}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            {[company.ticker, company.sector, company.exchange].filter(Boolean).join(' · ')}
          </div>
        </div>
        <div style={{ display: 'grid', gap: '8px', justifyItems: 'end' }}>
          <VerificationBadge level={company.verification_level} />
          <div style={{ fontSize: '20px', fontWeight: 700 }}>{company.ranking.total_score.toFixed(1)}</div>
        </div>
      </div>
      <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.6 }}>
        {summary || company.short_summary || 'No deterministic summary available.'}
      </div>
      <Link
        href={`/startup-hub/company/${company.slug}`}
        style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 700, fontSize: '13px' }}
      >
        Open detail
      </Link>
    </article>
  );
}

export default function StartupComparisonPanel({
  companies,
  selectedLeftSlug,
  selectedRightSlug,
  onLeftChange,
  onRightChange,
  onCompare,
  isLoading,
  error,
  response,
  fixedLeftCompany,
}: StartupComparisonPanelProps) {
  const rightOptions = companies.filter((company) => company.slug !== selectedLeftSlug);
  const leftOptions = companies.filter((company) => company.slug !== selectedRightSlug);
  const canCompare = Boolean(selectedLeftSlug && selectedRightSlug && selectedLeftSlug !== selectedRightSlug);

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
      <div style={{ display: 'grid', gap: '6px' }}>
        <div className="grid-label">Startup Comparison</div>
        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          Compare two public Startup Hub companies using stored growth, quality, risk, momentum, verification, and transparency fields.
        </div>
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'end' }}>
        {fixedLeftCompany ? (
          <div style={{ display: 'grid', gap: '6px' }}>
            <span className="grid-label">Left Company</span>
            <div
              style={{
                border: '1px solid var(--border)',
                background: 'var(--bg-elevated)',
                padding: '10px 12px',
                minWidth: '220px',
                fontWeight: 700,
              }}
            >
              {fixedLeftCompany.company_name}
            </div>
          </div>
        ) : (
          <SelectField
            label="Left Company"
            value={selectedLeftSlug}
            onChange={onLeftChange}
            companies={leftOptions}
          />
        )}

        <SelectField
          label="Right Company"
          value={selectedRightSlug}
          onChange={onRightChange}
          companies={rightOptions}
        />

        <button
          type="button"
          onClick={onCompare}
          disabled={!canCompare || isLoading}
          style={{
            border: '1px solid var(--border)',
            background: !canCompare || isLoading ? 'var(--bg-elevated)' : '#EFF6FF',
            color: !canCompare || isLoading ? 'var(--text-secondary)' : 'var(--primary)',
            padding: '10px 14px',
            fontWeight: 700,
            cursor: !canCompare || isLoading ? 'default' : 'pointer',
          }}
        >
          {isLoading ? 'Comparing...' : 'Run Comparison'}
        </button>
      </div>

      {error ? (
        <div
          style={{
            border: '1px solid #FECACA',
            background: '#FEF2F2',
            color: '#991B1B',
            padding: '12px',
            fontSize: '13px',
          }}
        >
          {error}
        </div>
      ) : null}

      {response?.stale ? (
        <StartupStaleBanner message={response.stale_message} cacheStatus={response.cache_status} />
      ) : null}

      {response ? (
        <div style={{ display: 'grid', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            <CompanySummary company={response.left} summary={response.left_summary} />
            <CompanySummary company={response.right} summary={response.right_summary} />
          </div>

          <section
            style={{
              border: '1px solid var(--border)',
              background: 'var(--bg-elevated)',
              padding: '16px',
              display: 'grid',
              gap: '12px',
            }}
          >
            <div className="grid-label">Category Winners</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px' }}>
              {Object.entries(response.category_winners).map(([category, winner]) => (
                <div
                  key={category}
                  style={{
                    border: '1px solid var(--border)',
                    background: 'var(--bg-surface)',
                    padding: '10px',
                    display: 'grid',
                    gap: '4px',
                  }}
                >
                  <div className="grid-label">{category}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{winner}</div>
                </div>
              ))}
            </div>
          </section>

          <section
            style={{
              border: '1px solid #DBEAFE',
              background: '#EFF6FF',
              padding: '16px',
              display: 'grid',
              gap: '10px',
            }}
          >
            <div className="grid-label" style={{ color: 'var(--primary)' }}>Comparison Summary</div>
            <div style={{ color: 'var(--foreground)', lineHeight: 1.6 }}>{response.overall_summary}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.6 }}>
              {response.ai_explanation || 'No deterministic explanation available.'}
            </div>
            {response.comparison_notes.length > 0 ? (
              <div style={{ display: 'grid', gap: '8px' }}>
                {response.comparison_notes.map((note) => (
                  <div
                    key={note}
                    style={{
                      border: '1px solid var(--border)',
                      background: 'rgba(255,255,255,0.7)',
                      padding: '10px 12px',
                      color: 'var(--text-secondary)',
                      fontSize: '13px',
                    }}
                  >
                    {note}
                  </div>
                ))}
              </div>
            ) : null}
          </section>
        </div>
      ) : null}
    </section>
  );
}
