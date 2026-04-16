import CompanyDetailClient from './CompanyDetailClient';

/**
 * Static export requirement for dynamic routes.
 * We return an empty array because we want client-side routing to handle 
 * all slugs at runtime via the SPA fallback (index.html).
 */
export function generateStaticParams() {
  return [{ slug: 'placeholder' }];
}

export default function StartupCompanyDetailPage() {
  return <CompanyDetailClient />;
}
