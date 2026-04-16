'use client';

import Link from 'next/link';
import { useDeferredValue, useEffect, useState } from 'react';

import StartupCardGrid from '@/components/startup-hub/StartupCardGrid';
import StartupComparisonPanel from '@/components/startup-hub/StartupComparisonPanel';
import StartupDisclaimer from '@/components/startup-hub/StartupDisclaimer';
import StartupEmptyState from '@/components/startup-hub/StartupEmptyState';
import StartupFilters from '@/components/startup-hub/StartupFilters';
import StartupHubSearch from '@/components/startup-hub/StartupHubSearch';
import StartupLoadingState from '@/components/startup-hub/StartupLoadingState';
import StartupStaleBanner from '@/components/startup-hub/StartupStaleBanner';
import StartupTable from '@/components/startup-hub/StartupTable';
import {
  fetchStartupCompanies,
  fetchStartupComparison,
  formatStartupTimestamp,
  type StartupCompareResponse,
  type StartupCompaniesResponse,
  type StartupCompanyListItem,
} from '@/utils/startupHubApi';

type SortOption = 'score_desc' | 'company_asc' | 'updated_desc';
type ViewMode = 'card' | 'table';

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

export default function StartupStocksPage() {
  const [data, setData] = useState<StartupCompaniesResponse | null>(null);
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('all');
  const [verification, setVerification] = useState('all');
  const [sort, setSort] = useState<SortOption>('score_desc');
  const [view, setView] = useState<ViewMode>('table');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [leftCompareSlug, setLeftCompareSlug] = useState('');
  const [rightCompareSlug, setRightCompareSlug] = useState('');
  const [compareError, setCompareError] = useState<string | null>(null);
  const [compareResult, setCompareResult] = useState<StartupCompareResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const deferredSearch = useDeferredValue(search);

  useEffect(() => {
    let isActive = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetchStartupCompanies({ entityType: 'public_stock' });
        if (isActive) {
          setData(response);
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError instanceof Error ? loadError.message : 'Failed to load startup stocks.');
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

  const runComparison = async () => {
    if (!leftCompareSlug || !rightCompareSlug || leftCompareSlug === rightCompareSlug) {
      setCompareError('Select two different companies to compare.');
      setCompareResult(null);
      return;
    }

    setIsComparing(true);
    setCompareError(null);
    try {
      const response = await fetchStartupComparison(leftCompareSlug, rightCompareSlug);
      setCompareResult(response);
    } catch (loadError) {
      setCompareError(loadError instanceof Error ? loadError.message : 'Failed to compare Startup Hub companies.');
      setCompareResult(null);
    } finally {
      setIsComparing(false);
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
          <div className="grid-label">Public Startup Stocks</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'end', flexWrap: 'wrap' }}>
            <div style={{ display: 'grid', gap: '8px' }}>
              <h1 style={{ fontSize: '32px', lineHeight: 1.05 }}>Deterministic public startup stock coverage.</h1>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '760px' }}>
                Browse the DB-backed Startup Hub universe. Scores, verification badges, and summaries come from the existing financial analysis engine and Startup Hub ranking layer.
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

        <StartupComparisonPanel
          companies={companies}
          selectedLeftSlug={leftCompareSlug}
          selectedRightSlug={rightCompareSlug}
          onLeftChange={setLeftCompareSlug}
          onRightChange={setRightCompareSlug}
          onCompare={() => void runComparison()}
          isLoading={isComparing}
          error={compareError}
          response={compareResult}
        />

        {data?.stale ? (
          <StartupStaleBanner message={data.stale_message} cacheStatus={data.cache_status} />
        ) : null}

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
          view={view}
          onViewChange={setView}
        />

        {isLoading ? <StartupLoadingState label="Loading startup stocks..." /> : null}
        {!isLoading && error ? (
          <StartupEmptyState title="Could not load startup stocks" message={error} actionHref="/startup-hub" actionLabel="Back to Startup Hub" />
        ) : null}
        {!isLoading && !error && filteredCompanies.length === 0 ? (
          <StartupEmptyState
            title="No startup stocks match the current filters"
            message="Try a different search term, clear the sector filter, or switch back to all verification states."
          />
        ) : null}
        {!isLoading && !error && filteredCompanies.length > 0 ? (
          view === 'card' ? <StartupCardGrid companies={filteredCompanies} /> : <StartupTable companies={filteredCompanies} />
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
