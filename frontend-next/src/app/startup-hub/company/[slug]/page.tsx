'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

import StartupComparisonPanel from '@/components/startup-hub/StartupComparisonPanel';
import StartupDetailHeader from '@/components/startup-hub/StartupDetailHeader';
import StartupDisclaimer from '@/components/startup-hub/StartupDisclaimer';
import StartupEmptyState from '@/components/startup-hub/StartupEmptyState';
import StartupLoadingState from '@/components/startup-hub/StartupLoadingState';
import StartupMetricsGrid from '@/components/startup-hub/StartupMetricsGrid';
import StartupRisksPanel from '@/components/startup-hub/StartupRisksPanel';
import StartupScoreBreakdown from '@/components/startup-hub/StartupScoreBreakdown';
import StartupSourcesPanel from '@/components/startup-hub/StartupSourcesPanel';
import StartupStaleBanner from '@/components/startup-hub/StartupStaleBanner';
import StartupThesisPanel from '@/components/startup-hub/StartupThesisPanel';
import {
  fetchStartupCompanies,
  fetchStartupComparison,
  fetchStartupCompanyDetail,
  formatStartupTimestamp,
  type StartupCompareResponse,
  type StartupCompaniesResponse,
  type StartupCompanyDetailResponse,
} from '@/utils/startupHubApi';

export default function StartupCompanyDetailPage() {
  const params = useParams<{ slug?: string | string[] }>();
  const slugValue = Array.isArray(params?.slug) ? params.slug[0] : params?.slug;
  const [data, setData] = useState<StartupCompanyDetailResponse | null>(null);
  const [companiesData, setCompaniesData] = useState<StartupCompaniesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [compareTargetSlug, setCompareTargetSlug] = useState('');
  const [compareError, setCompareError] = useState<string | null>(null);
  const [compareResult, setCompareResult] = useState<StartupCompareResponse | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  useEffect(() => {
    if (!slugValue) {
      setData(null);
      setError('No company slug was provided for this route.');
      setIsLoading(false);
      return;
    }

    let isActive = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetchStartupCompanyDetail(slugValue);
        if (isActive) {
          setData(response);
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError instanceof Error ? loadError.message : 'Failed to load company detail.');
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
  }, [slugValue]);

  useEffect(() => {
    let isActive = true;

    const loadCompanies = async () => {
      try {
        const response = await fetchStartupCompanies({ entityType: 'public_stock' });
        if (isActive) {
          setCompaniesData(response);
        }
      } catch {
        if (isActive) {
          setCompaniesData(null);
        }
      }
    };

    void loadCompanies();
    return () => {
      isActive = false;
    };
  }, []);

  const runComparison = async () => {
    if (!data?.company.slug || !compareTargetSlug || data.company.slug === compareTargetSlug) {
      setCompareError('Select a different company to compare against this detail page.');
      setCompareResult(null);
      return;
    }

    setIsComparing(true);
    setCompareError(null);
    try {
      const response = await fetchStartupComparison(data.company.slug, compareTargetSlug);
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
        minHeight: '100vh',
        background: 'var(--background)',
        color: 'var(--foreground)',
        padding: '32px 20px 40px',
      }}
    >
      <div style={{ maxWidth: '1180px', margin: '0 auto', display: 'grid', gap: '18px' }}>
        <section
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: '12px',
            flexWrap: 'wrap',
            alignItems: 'center',
          }}
        >
          <div className="grid-label">Startup Hub Detail View</div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <Link
              href="/startup-hub"
              style={{
                border: '1px solid var(--border)',
                background: 'var(--bg-surface)',
                padding: '10px 14px',
                color: 'var(--foreground)',
                textDecoration: 'none',
                fontWeight: 700,
              }}
            >
              Startup Hub Home
            </Link>
            <Link
              href="/startup-hub/stocks"
              style={{
                border: '1px solid var(--border)',
                background: 'var(--bg-elevated)',
                padding: '10px 14px',
                color: 'var(--foreground)',
                textDecoration: 'none',
                fontWeight: 700,
              }}
            >
              Back To Startup Stocks
            </Link>
          </div>
        </section>

        {data?.stale ? (
          <StartupStaleBanner message={data.stale_message} cacheStatus={data.cache_status} />
        ) : null}

        {isLoading ? <StartupLoadingState label="Loading company detail..." /> : null}

        {!isLoading && error ? (
          <StartupEmptyState
            title="Could not load company detail"
            message={error}
            actionHref="/startup-hub/stocks"
            actionLabel="Return To Startup Stocks"
          />
        ) : null}

        {!isLoading && !error && !data ? (
          <StartupEmptyState
            title="Company detail is unavailable"
            message="The selected company does not have a stored Startup Hub detail payload yet."
            actionHref="/startup-hub/stocks"
            actionLabel="Open Startup Stocks"
          />
        ) : null}

        {!isLoading && !error && data ? (
          <>
            <StartupDetailHeader
              company={data.company}
              verification={data.verification}
              description={data.description}
              lastUpdated={data.last_updated}
            />

            <section
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '18px',
              }}
            >
              <StartupScoreBreakdown ranking={data.company.ranking} />
              <StartupThesisPanel
                thesisSummary={data.thesis_summary}
                longSummary={data.long_summary}
                strengths={data.strengths}
              />
            </section>

            <StartupMetricsGrid metrics={data.metric_highlights} />

            <StartupComparisonPanel
              companies={(companiesData?.items || []).filter((company) => company.slug !== data.company.slug)}
              selectedLeftSlug={data.company.slug}
              selectedRightSlug={compareTargetSlug}
              onLeftChange={() => undefined}
              onRightChange={setCompareTargetSlug}
              onCompare={() => void runComparison()}
              isLoading={isComparing}
              error={compareError}
              response={compareResult}
              fixedLeftCompany={data.company}
            />

            <section
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '18px',
              }}
            >
              <StartupRisksPanel risks={data.risks} />
              <StartupSourcesPanel sources={data.sources} />
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
