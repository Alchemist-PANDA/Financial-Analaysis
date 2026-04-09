'use client';

import React from 'react';
import type { FinancialData } from './index';

type ProfitabilityPanelProps = {
    financialData: FinancialData;
};

const formatMetric = (value: number | undefined, suffix = '', precision = 1) => {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '--';
    }
    return `${value.toFixed(precision)}${suffix}`;
};

const ProfitabilityPanel = ({ financialData }: ProfitabilityPanelProps) => {
    const latest = financialData.yearly[financialData.yearly.length - 1];

    const rows = [
        { label: 'ROE', value: formatMetric(financialData.current_roe, '%') },
        { label: 'ROA', value: '--' },
        { label: 'ROIC', value: '--' },
        { label: 'Gross Margin', value: '--' },
        { label: 'EBITDA Margin', value: formatMetric(latest?.ebitda_margin, '%') },
        { label: 'Net Margin', value: formatMetric(latest?.net_margin, '%') },
    ];

    return (
        <article className="metrics-card">
            <h3 className="grid-label">Profitability</h3>
            <table className="terminal-table">
                <tbody>
                    {rows.map((row) => (
                        <tr key={row.label}>
                            <td>{row.label}</td>
                            <td>{row.value}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <style jsx>{`
                .metrics-card {
                    border: 1px solid var(--border);
                    background: #040404;
                    padding: 16px;
                }

                .grid-label {
                    margin-bottom: 12px;
                    display: block;
                }

                .terminal-table td:last-child {
                    color: var(--primary);
                    font-family: var(--font-mono);
                    text-align: right;
                }
            `}</style>
        </article>
    );
};

export default ProfitabilityPanel;
