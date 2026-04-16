'use client';

import Link from 'next/link';
import { useDeferredValue, useEffect, useState } from 'react';

import StartupCardGrid from '@/components/startup-hub/StartupCardGrid';
import StartupAgentPanel from '@/components/startup-hub/StartupAgentPanel';
import StartupDisclaimer from '@/components/startup-hub/StartupDisclaimer';
import StartupEmptyState from '@/components/startup-hub/StartupEmptyState';
import StartupFilters from '@/components/startup-hub/StartupFilters';
import StartupHubHero from '@/components/startup-hub/StartupHubHero';
import StartupHubSearch from '@/components/startup-hub/StartupHubSearch';
import StartupLoadingState from '@/components/startup-hub/StartupLoadingState';
import StartupRankingList from '@/components/startup-hub/StartupRankingList';
import StartupStaleBanner from '@/components/startup-hub/StartupStaleBanner';
import {
  fetchStartupHubHome,
  formatStartupTimestamp,
  submitStartupAgentQuery,
  type StartupAgentQueryResponse,
  type StartupCompanyListItem,
  type StartupHubHomeResponse,
} from '@/utils/startupHubApi';

type SortOption = 'score_desc' | 'company_asc' | 'updated_desc';

const AGENT_PROMPTS = [
  'best AI startups with strongest fundamentals',
  'compare c3.ai vs duolingo',
  'explain why this ranks first',
  'show lower-risk startup opportunities',
  'summarize this IPO candidate',
];

function sortCompanies(companies: StartupCompanyListItem[], sort: SortOption) {
  const items = [...companies];
  if (sort === 'company_asc') {
    items.sort((left, right) => left.company_name.localeCompare(right.company_name));
    return items;
  }
  if (sort === 'updated_desc') {
    items.sort((left, right) => {
      const leftTime = left.last_updated ? new Date(left.last_updated).getTime() : 0;
      const rightTime = right.last_updated ? new Date(right.last_updated).getTime() : 0;
      return rightTime - leftTime;
    });
    return items;
  }
  items.sort((left, right) => right.ranking.total_score - left.ranking.total_score);
  return items;
}

export default function StartupHubPage() {
  const [data, setData] = useState<StartupHubHomeResponse | null>(null);
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('all');
  const [verification, setVerification] = useState('all');
  const [sort, setSort] = useState<SortOption>('score_desc');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [agentQuery, setAgentQuery] = useState('best AI startups with strongest fundamentals');
  const [agentResponse, setAgentResponse] = useState<StartupAgentQueryResponse | null>(null);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [isAgentLoading, setIsAgentLoading] = useState(false);
  const deferredSearch = useDeferredValue(search);

  useEffect(() => {
    let isActive = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetchStartupHubHome();
        if (isActive) {
          setData(response);
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError instanceof Error ? loadError.message : 'Failed to load Startup Hub.');
          setData(null);
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    void load();
    return () => {
      isActive = false;
    };
  }, []);

  const companies = data?.public_companies || [];
  const sectorOptions = [
    { label: 'All sectors', value: 'all' },
    ...Array.from(new Set(companies.map((company) => company.sector).filter(Boolean)))
      .sort((left, right) => String(left).localeCompare(String(right)))
      .map((option) => ({ label: option as string, value: option as string })),
  ];

  const filteredCompanies = sortCompanies(
    companies.filter((company) => {
      const searchValue = deferredSearch.trim().toLowerCase();
      const matchesSearch =
        !searchValue ||
        company.company_name.toLowerCase().includes(searchValue) ||
        (company.ticker || '').toLowerCase().includes(searchValue) ||
        (company.sector || '').toLowerCase().includes(searchValue);
      const matchesSector = sector === 'all' || company.sector === sector;
      const matchesVerification = verification === 'all' || company.verification_level === verification;
      return matchesSearch && matchesSector && matchesVerification;
    }),
    sort
  );

  const topCompany = sortCompanies(companies, 'score_desc')[0];

  const runAgentQuery = async (queryOverride?: string) => {
    const nextQuery = (queryOverride ?? agentQuery).trim();
    if (!nextQuery) {
      return;
    }

    setIsAgentLoading(true);
    setAgentError(null);
    try {
      const response = await submitStartupAgentQuery({
        query: nextQuery,
        include_explanations: true,
        limit: 5,
      });
      setAgentResponse(response);
      setAgentQuery(nextQuery);
    } catch (loadError) {
      setAgentError(loadError instanceof Error ? loadError.message : 'Failed to run Startup Hub research query.');
      setAgentResponse(null);
    } finally {
      setIsAgentLoading(false);
    }
  };

  return (
    <main
      style={{
        height: '100vh',
        overflowY: 'auto',
        background: 'var(--background)',
        color: 'var(--foreground)',
        padding: '32px 20px 40px',
      }}
    >
      <div style={{ maxWidth: '1180px', margin: '0 auto', display: 'grid', gap: '18px' }}>
        <StartupHubHero
          title="Startup discovery backed by the existing financial analysis engine."
          description="Startup Hub ranks public startup-like companies using deterministic financial signals, source verification, and transparent scoring. It is a research workspace, not a brokerage flow."
          companyCount={companies.length}
          topCompanyName={topCompany?.company_name}
          topCompanyScore={topCompany?.ranking.total_score}
          lastUpdated={formatStartupTimestamp(data?.last_updated || null)}
        />

        <StartupAgentPanel
          query={agentQuery}
          onQueryChange={setAgentQuery}
          onSubmit={() => void runAgentQuery()}
          onPromptSelect={(value) => {
            setAgentQuery(value);
            void runAgentQuery(value);
          }}
          isLoading={isAgentLoading}
          error={agentError}
          response={agentResponse}
          promptSuggestions={AGENT_PROMPTS}
        />

        {isLoading ? <StartupLoadingState label="Loading Startup Hub home..." /> : null}
        {!isLoading && error ? (
          <StartupEmptyState
            title="Could not load Startup Hub"
            message={error}
            actionHref="/startup-hub/stocks"
            actionLabel="Open Startup Stocks"
          />
        ) : null}

        {data?.stale ? (
          <StartupStaleBanner message={data.stale_message} cacheStatus={data.cache_status} />
        ) : null}

        {!isLoading && !error && data ? (
          <>
            <section
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '18px',
              }}
            >
              <div style={{ display: 'grid', gap: '18px' }}>
                <StartupHubSearch value={search} onChange={setSearch} />
                <StartupFilters
                  sectorOptions={sectorOptions}
                  verificationOptions={[
                    { label: 'All verification', value: 'all' },
                    { label: 'Verified Public', value: 'verified_public' },
                    { label: 'Partial', value: 'partial' },
                    { label: 'Unverified', value: 'unverified' },
                  ]}
                  sortOptions={[
                    { label: 'Highest score', value: 'score_desc' },
                    { label: 'Company A-Z', value: 'company_asc' },
                    { label: 'Recently updated', value: 'updated_desc' },
                  ]}
                  selectedSector={sector}
                  selectedVerification={verification}
                  selectedSort={sort}
                  onSectorChange={setSector}
                  onVerificationChange={setVerification}
                  onSortChange={(value) => setSort(value as SortOption)}
                />
              </div>
              <StartupRankingList companies={sortCompanies(companies, 'score_desc').slice(0, 5)} />
            </section>

            <section style={{ display: 'grid', gap: '12px' }}>
              <div className="grid-label">Featured Public Startups</div>
              {data.featured.length > 0 ? (
                <StartupCardGrid companies={data.featured} />
              ) : (
                <StartupEmptyState
                  title="No featured companies yet"
                  message="Public startup records have not been refreshed yet."
                />
              )}
            </section>

            {data.ipo_preview.length > 0 ? (
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
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <div style={{ display: 'grid', gap: '4px' }}>
                    <div className="grid-label">IPO Watch Preview</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                      IPO candidates are modeled separately from public startup stocks.
                    </div>
                  </div>
                  <Link
                    href="/startup-hub/ipos"
                    style={{
                      display: 'inline-flex',
                      padding: '10px 14px',
                      border: '1px solid var(--border)',
                      background: 'var(--bg-elevated)',
                      color: 'var(--foreground)',
                      textDecoration: 'none',
                      fontWeight: 700,
                    }}
                  >
                    Open IPO Watch
                  </Link>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
                  {data.ipo_preview.map((company) => (
                    <div
                      key={company.slug}
                      style={{
                        border: '1px solid var(--border)',
                        background: 'var(--bg-elevated)',
                        padding: '14px',
                        display: 'grid',
                        gap: '8px',
                      }}
                    >
                      <div style={{ fontSize: '18px', fontWeight: 700 }}>{company.company_name}</div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                        {[company.sector, company.status_label].filter(Boolean).join(' · ') || 'IPO watch entry'}
                      </div>
                      <div style={{ fontSize: '20px', fontWeight: 700 }}>{company.ranking.total_score.toFixed(1)}</div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
                        {company.ranking.red_flags[0] || company.short_summary || 'Incomplete data is clearly labeled.'}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            <section style={{ display: 'grid', gap: '12px' }}>
              <div className="grid-label">Filtered Public Startup Stocks</div>
              {filteredCompanies.length > 0 ? (
                <StartupCardGrid companies={filteredCompanies.slice(0, 6)} />
              ) : (
                <StartupEmptyState
                  title="No companies match the current filters"
                  message="Try clearing the search term or widening the verification and sector filters."
                />
              )}
            </section>

            <StartupDisclaimer
              items={data.disclaimer}
              lastUpdated={formatStartupTimestamp(data.last_updated)}
            />
          </>
        ) : null}
      </div>
    </main>
  );
}
