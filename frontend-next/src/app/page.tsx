'use client';

import Sidebar from "@/components/Sidebar";
import MainTerminal from "@/components/MainTerminal";
import { useState } from "react";

import ComparisonTerminal from "@/components/ComparisonTerminal";
import MetricsPanel, { type FinancialData } from "@/components/MetricsPanel";
import ComparisonBoard from "@/components/ComparisonBoard";
import { FEATURES } from "@/config/features";

const EMPTY_FINANCIAL_DATA: FinancialData = {
  yearly: [
    {
      year: 'Y0',
      revenue: 0,
      ebitda: 0,
      net_income: 0,
      ebitda_margin: 0,
      net_margin: 0,
      net_debt: 0,
      leverage: 0,
      asset_turnover: 0,
      equity_multiplier: 0,
      roe: 0,
      dso: 0,
      inventory_turnover: 0,
      fcf_conversion_pct: 0,
      z_score: 0,
    },
  ],
  revenue_cagr_pct: 0,
  revenue_trajectory: 'STEADY',
  margin_signal: 'STABLE',
  debt_signal: 'STABLE',
  solvency_signal: 'GREY_ZONE',
  current_z_score: 0,
  current_roe: 0,
  current_dso: 0,
  current_inventory_turnover: 0,
  current_fcf_conversion_pct: 0,
};

export default function Home() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [currentView, setCurrentView] = useState<'live' | 'compare'>('live');

  const handleAnalysisComplete = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="terminal-main">
      <Sidebar
        onSelectTicker={(t) => { setSelectedTicker(t); setCurrentView('live'); }}
        refreshTrigger={refreshTrigger}
        currentView={currentView}
        onViewChange={setCurrentView}
      />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {currentView === 'live' ? (
          <MainTerminal
            forceTicker={selectedTicker}
            onAnalysisComplete={handleAnalysisComplete}
          />
        ) : (
          <ComparisonTerminal />
        )}

        {FEATURES.METRICS_PANEL && (
          <div style={{ padding: '16px', borderTop: '1px solid var(--border)', background: '#020202' }}>
            <MetricsPanel financialData={EMPTY_FINANCIAL_DATA} />
          </div>
        )}

        {FEATURES.COMPARISON_BOARD && (
          <div style={{ padding: '16px', borderTop: '1px solid var(--border)', background: '#020202' }}>
            <ComparisonBoard
              companyA={EMPTY_FINANCIAL_DATA}
              companyB={EMPTY_FINANCIAL_DATA}
              industryAverage={EMPTY_FINANCIAL_DATA}
              companyALabel="Company A"
              companyBLabel="Company B"
            />
          </div>
        )}
      </div>
    </div>
  );
}
