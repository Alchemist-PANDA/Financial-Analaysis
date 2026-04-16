import type { StartupCompanyListItem } from '@/utils/startupHubApi';
import StartupCard from '@/components/startup-hub/StartupCard';

type StartupCardGridProps = {
  companies: StartupCompanyListItem[];
};

export default function StartupCardGrid({ companies }: StartupCardGridProps) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
      }}
    >
      {companies.map((company) => (
        <StartupCard key={company.slug} company={company} />
      ))}
    </div>
  );
}
