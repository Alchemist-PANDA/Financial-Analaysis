'use client';

import React from 'react';
import ProfitabilityPanel from './ProfitabilityPanel';
import SolvencyPanel from './SolvencyPanel';
import LiquidityPanel from './LiquidityPanel';
import ValuationPanel from './ValuationPanel';
import GrowthPanel from './GrowthPanel';

export type CalculatorYearMetric = {
    year: string;
    revenue: number;
    ebitda: number;
    net_income: number;
    ebitda_margin: number;
    net_margin: number;
    net_debt: number;
    leverage: number;
    asset_turnover: number;
    equity_multiplier: number;
    roe: number;
    dso: number;
    inventory_turnover: number;
    fcf_conversion_pct: number;
    z_score: number;
    roa: number;
    gross_margin: number;
    debt_equity: number;
    current_ratio: number;
    quick_ratio: number;
    cash_ratio: number;
    interest_coverage: number;
    pe_ratio: number;
    pb_ratio: number;
    ev_ebitda: number;
};

export type FinancialData = {
    yearly: CalculatorYearMetric[];
    revenue_cagr_pct: number;
    revenue_trajectory: string;
    margin_signal: string;
    debt_signal: string;
    solvency_signal: string;
    current_z_score: number;
    current_roe: number;
    current_roa: number;
    current_gross_margin: number;
    current_debt_equity: number;
    current_ratio: number;
    current_quick_ratio: number;
    current_cash_ratio: number;
    current_interest_coverage: number;
    current_pe_ratio: number;
    current_pb_ratio: number;
    current_ev_ebitda: number;
    current_dso: number;
    current_inventory_turnover: number;
    current_fcf_conversion_pct: number;
};

type MetricsPanelProps = {
    financialData: FinancialData;
};

const MetricsPanel = ({ financialData }: MetricsPanelProps) => {
    return (
        <section className="metrics-panel-grid">
            <ProfitabilityPanel financialData={financialData} />
            <SolvencyPanel financialData={financialData} />
            <LiquidityPanel financialData={financialData} />
            <ValuationPanel financialData={financialData} />
            <GrowthPanel financialData={financialData} />

            <style jsx>{`
                .metrics-panel-grid {
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 16px;
                }

                @media (max-width: 1100px) {
                    .metrics-panel-grid {
                        grid-template-columns: 1fr;
                    }
                }
            `}</style>
        </section>
    );
};

export default MetricsPanel;
