'use client';

import React from 'react';

type MetricRowProps = {
    metricName: string;
    companyAValue: number;
    companyBValue: number;
    industryAverageValue: number;
    higherIsBetter?: boolean;
};

const formatValue = (value: number, suffix = '', precision = 2) => {
    if (!Number.isFinite(value)) {
        return '--';
    }
    return `${value.toFixed(precision)}${suffix}`;
};

const MetricRow = ({
    metricName,
    companyAValue,
    companyBValue,
    industryAverageValue,
    higherIsBetter = true,
}: MetricRowProps) => {
    const beatsIndustry = (value: number) => {
        if (!Number.isFinite(value) || !Number.isFinite(industryAverageValue)) {
            return false;
        }
        return higherIsBetter ? value >= industryAverageValue : value <= industryAverageValue;
    };

    const companyAClass = beatsIndustry(companyAValue) ? 'cell-win' : 'cell-loss';
    const companyBClass = beatsIndustry(companyBValue) ? 'cell-win' : 'cell-loss';

    return (
        <div className="metric-row">
            <div className="metric-cell metric-name">{metricName}</div>
            <div className={`metric-cell ${companyAClass}`}>{formatValue(companyAValue)}</div>
            <div className={`metric-cell ${companyBClass}`}>{formatValue(companyBValue)}</div>
            <div className="metric-cell industry-cell">{formatValue(industryAverageValue)}</div>

            <style jsx>{`
                .metric-row {
                    display: grid;
                    grid-template-columns: 220px 180px 180px 180px;
                    border-bottom: 1px solid var(--border);
                }

                .metric-cell {
                    padding: 10px 12px;
                    font-family: var(--font-mono);
                    font-size: 12px;
                    border-right: 1px solid var(--border);
                }

                .metric-cell:last-child {
                    border-right: none;
                }

                .metric-name {
                    color: var(--foreground);
                    background: rgba(255, 255, 255, 0.02);
                    font-family: var(--font-sans);
                    font-size: 13px;
                }

                .cell-win {
                    color: #00ff41;
                    background: rgba(0, 255, 65, 0.08);
                }

                .cell-loss {
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.08);
                }

                .industry-cell {
                    color: var(--text-muted);
                    background: rgba(255, 255, 255, 0.02);
                }
            `}</style>
        </div>
    );
};

export default MetricRow;
