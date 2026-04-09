'use client';

import React from 'react';
import type { FinancialData } from './index';

type ValuationPanelProps = {
    financialData: FinancialData;
};

const formatMetric = (value: number | undefined, suffix = '', precision = 1) => {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '--';
    }
    return `${value.toFixed(precision)}${suffix}`;
};

const ValuationPanel = ({ financialData }: ValuationPanelProps) => {
    void financialData;

    const rows = [
        { label: 'P/E', value: formatMetric(financialData.current_pe_ratio, '', 1) },
        { label: 'P/B', value: formatMetric(financialData.current_pb_ratio, '', 1) },
        { label: 'EV/EBITDA', value: formatMetric(financialData.current_ev_ebitda, '', 1) },
        { label: 'PEG Ratio', value: '--' },
        { label: 'DCF Intrinsic Value', value: '--' },
    ];

    return (
        <article className="metrics-card">
            <h3 className="grid-label">Valuation</h3>
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

export default ValuationPanel;
