'use client';

import React from 'react';
import type { FinancialData } from './index';

type GrowthPanelProps = {
    financialData: FinancialData;
};

const formatMetric = (value: number | undefined, suffix = '', precision = 1) => {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '--';
    }
    return `${value.toFixed(precision)}${suffix}`;
};

const GrowthPanel = ({ financialData }: GrowthPanelProps) => {
    const rows = [
        { label: 'Revenue CAGR', value: formatMetric(financialData.revenue_cagr_pct, '%') },
        { label: 'EPS Growth', value: '--' },
        { label: 'FCF Growth', value: '--' },
    ];

    return (
        <article className="metrics-card metrics-card-full">
            <h3 className="grid-label">Growth</h3>
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
            <p className="signal-line">Trajectory: {financialData.revenue_trajectory}</p>

            <style jsx>{`
                .metrics-card {
                    border: 1px solid var(--border);
                    background: #040404;
                    padding: 16px;
                }

                .metrics-card-full {
                    grid-column: 1 / -1;
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

                .signal-line {
                    margin-top: 12px;
                    color: var(--text-muted);
                    font-size: 12px;
                }
            `}</style>
        </article>
    );
};

export default GrowthPanel;
