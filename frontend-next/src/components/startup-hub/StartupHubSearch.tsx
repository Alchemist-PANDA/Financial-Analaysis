type StartupHubSearchProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

export default function StartupHubSearch({
  value,
  onChange,
  placeholder = 'Search by company, ticker, or sector',
}: StartupHubSearchProps) {
  return (
    <section
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: 'var(--shadow-card)',
        padding: '18px 20px',
        display: 'grid',
        gap: '10px',
      }}
    >
      <div className="grid-label">Search</div>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%',
          border: '1px solid var(--border)',
          padding: '12px 14px',
          background: 'var(--bg-elevated)',
          color: 'var(--foreground)',
          fontSize: '14px',
          outline: 'none',
        }}
      />
    </section>
  );
}
