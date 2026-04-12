'use client';

import React, { useEffect, useState, useRef } from 'react';

declare global {
  interface Window {
    TradingView: any;
  }
}

interface SignalData {
  ticker: string;
  price_change: number;
  explanation: string;
  confidence: number;
  signals: any;
}

const ChartIntelligence = ({ ticker }: { ticker: string }) => {
    const [intelligence, setIntelligence] = useState<SignalData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const BASE_URL = (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:7860').replace(/\\n/g, '').trim();

    useEffect(() => {
        if (!ticker) return;

        const fetchIntelligence = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const res = await fetch(`${BASE_URL}/api/explain-chart?ticker=${ticker}`);
                if (!res.ok) throw new Error('Intelligence engine unavailable');
                const data = await res.json();
                setIntelligence(data);
            } catch (err) {
                setError('Unable to generate AI chart analysis');
            } finally {
                setIsLoading(false);
            }
        };

        fetchIntelligence();

        // Initialize TradingView Widget
        if (window.TradingView && containerRef.current) {
            new window.TradingView.widget({
                "container_id": containerRef.current.id,
                "autosize": true,
                "symbol": ticker.includes(':') ? ticker : `NASDAQ:${ticker}`,
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#0f172a",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "details": true,
                "hotlist": true,
                "calendar": true,
                "show_popup_button": true,
                "popup_width": "1000",
                "popup_height": "650",
            });
        }
    }, [ticker, BASE_URL]);

    const getConfidenceColor = (score: number) => {
        if (score > 0.7) return '#059669'; // Green
        if (score > 0.4) return '#d97706'; // Yellow
        return '#dc2626'; // Red
    };

    return (
        <div className="intelligence-container">
            {/* AI Explanation Box */}
            <section className="explanation-card">
                <div className="card-header">
                    <div className="title-row">
                        <span className="icon">🧠</span>
                        <h3>CHART INTELLIGENCE</h3>
                        {intelligence && (
                            <span 
                                className="confidence-badge"
                                style={{ backgroundColor: getConfidenceColor(intelligence.confidence) }}
                            >
                                {(intelligence.confidence * 100).toFixed(0)}% CONFIDENT
                            </span>
                        )}
                    </div>
                </div>
                
                <div className="card-body">
                    {isLoading ? (
                        <div className="loading-text">Analyzing market signals...</div>
                    ) : error ? (
                        <div className="error-text">{error}</div>
                    ) : intelligence ? (
                        <p className="explanation-text">{intelligence.explanation}</p>
                    ) : (
                        <p className="explanation-text">Enter a ticker to begin forensic chart analysis.</p>
                    )}
                </div>
            </section>

            {/* TradingView Widget */}
            <div className="chart-wrapper">
                <div id="tv_chart_container" ref={containerRef} style={{ height: '500px' }} />
            </div>

            <style jsx>{`
                .intelligence-container {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                    padding: 16px;
                    height: 100%;
                    overflow-y: auto;
                }
                .explanation-card {
                    background: #1e293b;
                    border-left: 4px solid #0ea5e9;
                    padding: 16px;
                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                }
                .title-row {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 8px;
                }
                .title-row h3 {
                    font-size: 12px;
                    font-weight: 700;
                    letter-spacing: 0.05em;
                    color: #94a3b8;
                    margin: 0;
                }
                .confidence-badge {
                    font-size: 9px;
                    font-weight: 800;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 9999px;
                }
                .explanation-text {
                    font-size: 14px;
                    line-height: 1.6;
                    color: #f1f5f9;
                    margin: 0;
                }
                .loading-text {
                    color: #64748b;
                    font-size: 13px;
                    font-style: italic;
                }
                .error-text {
                    color: #ef4444;
                    font-size: 13px;
                }
                .chart-wrapper {
                    flex: 1;
                    min-height: 500px;
                    border: 1px solid #334155;
                    background: #0f172a;
                }
            `}</style>
        </div>
    );
};

export default ChartIntelligence;
