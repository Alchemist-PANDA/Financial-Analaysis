'use client';

import React from 'react';
import type { FinancialData } from './index';

type SolvencyPanelProps = {
    financialData: FinancialData;
};

const formatMetric = (value: number | undefined, suffix = '', precision = 2) => {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '--';
    }
    return `${value.toFixed(precision)}${suffix}`;
};

const SolvencyPanel = ({ financialData }: SolvencyPanelProps) => {
    const rows = [
        { label: 'Altman-Z', value: formatMetric(financialData.current_z_score, '', 2) },
        { label: 'Debt/Equity', value: '--' },
        { label: 'Interest Coverage', value: '--' },
        { label: 'Current Ratio', value: '--' },
    ];

    return (
        <article className="metrics-card">
            <h3 className="grid-label">Solvency</h3>
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
            <p className="signal-line">Signal: {financialData.solvency_signal}</p>

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

                .signal-line {
                    margin-top: 12px;
                    color: var(--text-muted);
                    font-size: 12px;
                }
            `}</style>
        </article>
    );
};

export default SolvencyPanel;
