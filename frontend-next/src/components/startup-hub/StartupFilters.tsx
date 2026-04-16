type FilterOption = {
  label: string;
  value: string;
};

type StartupFiltersProps = {
  sectorOptions: FilterOption[];
  verificationOptions: FilterOption[];
  sortOptions: FilterOption[];
  selectedSector: string;
  selectedVerification: string;
  selectedSort: string;
  onSectorChange: (value: string) => void;
  onVerificationChange: (value: string) => void;
  onSortChange: (value: string) => void;
  view?: 'card' | 'table';
  onViewChange?: (value: 'card' | 'table') => void;
};

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: FilterOption[];
}) {
  return (
    <label style={{ display: 'grid', gap: '6px' }}>
      <span className="grid-label">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={{
          border: '1px solid var(--border)',
          background: 'var(--bg-elevated)',
          padding: '10px 12px',
          color: 'var(--foreground)',
          minWidth: '160px',
        }}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function StartupFilters({
  sectorOptions,
  verificationOptions,
  sortOptions,
  selectedSector,
  selectedVerification,
  selectedSort,
  onSectorChange,
  onVerificationChange,
  onSortChange,
  view,
  onViewChange,
}: StartupFiltersProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '18px 20px',
        display: 'grid',
        gap: '14px',
      }}
    >
      <div className="grid-label">Filters</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'end' }}>
        <FilterSelect label="Sector" value={selectedSector} onChange={onSectorChange} options={sectorOptions} />
        <FilterSelect
          label="Verification"
          value={selectedVerification}
          onChange={onVerificationChange}
          options={verificationOptions}
        />
        <FilterSelect label="Sort" value={selectedSort} onChange={onSortChange} options={sortOptions} />
        {view && onViewChange ? (
          <div style={{ display: 'grid', gap: '6px' }}>
            <span className="grid-label">View</span>
            <div style={{ display: 'flex', gap: '8px' }}>
              {(['card', 'table'] as const).map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => onViewChange(option)}
                  style={{
                    border: '1px solid var(--border)',
                    background: view === option ? '#EFF6FF' : 'var(--bg-elevated)',
                    color: view === option ? 'var(--primary)' : 'var(--foreground)',
                    padding: '10px 12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {option === 'card' ? 'Cards' : 'Table'}
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
