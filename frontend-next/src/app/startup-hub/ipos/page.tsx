'use client';

import Link from 'next/link';
import { useDeferredValue, useEffect, useState } from 'react';

import IpoCard from '@/components/startup-hub/IpoCard';
import StartupDisclaimer from '@/components/startup-hub/StartupDisclaimer';
import StartupEmptyState from '@/components/startup-hub/StartupEmptyState';
import StartupFilters from '@/components/startup-hub/StartupFilters';
import StartupHubSearch from '@/components/startup-hub/StartupHubSearch';
import StartupLoadingState from '@/components/startup-hub/StartupLoadingState';
import StartupStaleBanner from '@/components/startup-hub/StartupStaleBanner';
import {
  fetchStartupIpos,
  formatStartupTimestamp,
  type StartupIpoListItem,
  type StartupIposResponse,
} from '@/utils/startupHubApi';

type SortOption = 'score_desc' | 'company_asc' | 'updated_desc';

function sortIpos(companies: StartupIpoListItem[], sort: SortOption) {
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

export default function StartupIposPage() {
  const [data, setData] = useState<StartupIposResponse | null>(null);
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('all');
  const [verification, setVerification] = useState('all');
  const [sort, setSort] = useState<SortOption>('score_desc');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const deferredSearch = useDeferredValue(search);

  useEffect(() => {
    let isActive = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetchStartupIpos();
        if (isActive) {
          setData(response);
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError instanceof Error ? loadError.message : 'Failed to load IPO Watch.');
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

  const companies = data?.items || [];
  const sectorOptions = [
    { label: 'All sectors', value: 'all' },
    ...Array.from(new Set(companies.map((company) => company.sector).filter(Boolean)))
      .sort((left, right) => String(left).localeCompare(String(right)))
      .map((option) => ({ label: option as string, value: option as string })),
  ];

  const filteredCompanies = sortIpos(
    companies.filter((company) => {
      const searchValue = deferredSearch.trim().toLowerCase();
      const matchesSearch =
        !searchValue ||
        company.company_name.toLowerCase().includes(searchValue) ||
        (company.sector || '').toLowerCase().includes(searchValue) ||
        (company.filing_status || '').toLowerCase().includes(searchValue);
      const matchesSector = sector === 'all' || company.sector === sector;
      const matchesVerification = verification === 'all' || company.verification_level === verification;
      return matchesSearch && matchesSector && matchesVerification;
    }),
    sort
  );

  return (
    <main
      style={{
        minHeight: '100vh',
        background: 'var(--background)',
        color: 'var(--foreground)',
        padding: '32px 20px 40px',
      }}
    >
      <div style={{ maxWidth: '1180px', margin: '0 auto', display: 'grid', gap: '18px' }}>
        <section
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            boxShadow: 'var(--shadow-card)',
            padding: '24px',
            display: 'grid',
            gap: '10px',
          }}
        >
          <div className="grid-label">IPO Watch</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'end', flexWrap: 'wrap' }}>
            <div style={{ display: 'grid', gap: '8px' }}>
              <h1 style={{ fontSize: '32px', lineHeight: 1.05 }}>Seeded IPO research coverage with explicit confidence limits.</h1>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '760px' }}>
                IPO Watch keeps pre-listing candidates separate from public stocks. Status, ranking, verification, and completeness are deterministic and should be verified against official filings and exchange sources.
              </p>
              <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                Last updated: {formatStartupTimestamp(data?.last_updated || null)}
              </div>
            </div>
            <Link
              href="/startup-hub"
              style={{
                display: 'inline-flex',
                padding: '10px 14px',
                border: '1px solid var(--border)',
                background: 'var(--bg-elevated)',
                color: 'var(--foreground)',
                textDecoration: 'none',
                fontWeight: 600,
              }}
            >
              Back To Hub
            </Link>
          </div>
        </section>

        {data?.stale ? (
          <StartupStaleBanner message={data.stale_message} cacheStatus={data.cache_status} />
        ) : null}

        <StartupHubSearch value={search} onChange={setSearch} />
        <StartupFilters
          sectorOptions={sectorOptions}
          verificationOptions={[
            { label: 'All verification', value: 'all' },
            { label: 'Verified IPO', value: 'verified_ipo' },
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

        {isLoading ? <StartupLoadingState label="Loading IPO Watch..." /> : null}
        {!isLoading && error ? (
          <StartupEmptyState
            title="Could not load IPO Watch"
            message={error}
            actionHref="/startup-hub"
            actionLabel="Back to Startup Hub"
          />
        ) : null}
        {!isLoading && !error && filteredCompanies.length === 0 ? (
          <StartupEmptyState
            title="No IPO candidates match the current filters"
            message="Try a different search term or clear the sector and verification filters."
          />
        ) : null}

        {!isLoading && !error && filteredCompanies.length > 0 ? (
          <section
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '16px',
            }}
          >
            {filteredCompanies.map((company) => (
              <IpoCard key={company.slug} company={company} />
            ))}
          </section>
        ) : null}

        {data ? (
          <StartupDisclaimer items={data.disclaimer} lastUpdated={formatStartupTimestamp(data.last_updated)} />
        ) : null}
      </div>
    </main>
  );
}
