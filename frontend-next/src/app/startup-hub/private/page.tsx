'use client';

import Link from 'next/link';
import { useDeferredValue, useEffect, useState } from 'react';

import PrivateOpportunityCard from '@/components/startup-hub/PrivateOpportunityCard';
import StartupDisclaimer from '@/components/startup-hub/StartupDisclaimer';
import StartupEmptyState from '@/components/startup-hub/StartupEmptyState';
import StartupFilters from '@/components/startup-hub/StartupFilters';
import StartupHubSearch from '@/components/startup-hub/StartupHubSearch';
import StartupLoadingState from '@/components/startup-hub/StartupLoadingState';
import StartupStaleBanner from '@/components/startup-hub/StartupStaleBanner';
import {
  fetchStartupPrivateOpportunities,
  formatStartupTimestamp,
  type StartupPrivateOpportunityItem,
  type StartupPrivateResponse,
} from '@/utils/startupHubApi';

type SortOption = 'score_desc' | 'company_asc' | 'updated_desc';

function sortPrivateOpportunities(companies: StartupPrivateOpportunityItem[], sort: SortOption) {
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

export default function StartupPrivatePage() {
  const [data, setData] = useState<StartupPrivateResponse | null>(null);
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
        const response = await fetchStartupPrivateOpportunities();
        if (isActive) {
          setData(response);
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError instanceof Error ? loadError.message : 'Failed to load private opportunities.');
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

  const filteredCompanies = sortPrivateOpportunities(
    companies.filter((company) => {
      const searchValue = deferredSearch.trim().toLowerCase();
      const matchesSearch =
        !searchValue ||
        company.company_name.toLowerCase().includes(searchValue) ||
        (company.sector || '').toLowerCase().includes(searchValue) ||
        (company.source_name || '').toLowerCase().includes(searchValue);
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
          <div className="grid-label">Private Opportunities</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'end', flexWrap: 'wrap' }}>
            <div style={{ display: 'grid', gap: '8px' }}>
              <h1 style={{ fontSize: '32px', lineHeight: 1.05 }}>Research-only private opportunity listings with explicit source limits.</h1>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '760px' }}>
                These entries are not tradable in this product. The page surfaces source transparency, verification level, and known terms without implying platform eligibility checks or direct purchase capability.
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
            { label: 'Source Verified', value: 'source_verified_private' },
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

        {isLoading ? <StartupLoadingState label="Loading private opportunities..." /> : null}
        {!isLoading && error ? (
          <StartupEmptyState
            title="Could not load private opportunities"
            message={error}
            actionHref="/startup-hub"
            actionLabel="Back to Startup Hub"
          />
        ) : null}
        {!isLoading && !error && filteredCompanies.length === 0 ? (
          <StartupEmptyState
            title="No private opportunities match the current filters"
            message="Try widening the verification filter or search for a different company or sector."
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
              <PrivateOpportunityCard key={company.slug} company={company} />
            ))}
          </section>
        ) : null}

        {data ? (
          <StartupDisclaimer
            items={data.disclaimer}
            lastUpdated={formatStartupTimestamp(data.last_updated)}
          />
        ) : null}
      </div>
    </main>
  );
}
