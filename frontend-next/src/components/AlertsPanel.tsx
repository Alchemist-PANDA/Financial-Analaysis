'use client';

import React, { useState, useEffect } from 'react';
import { getApiBaseUrl, safeFetch } from '@/utils/api';

interface WatchlistItem {
    ticker: string;
    lastPrice: number;
    change: number;
    explanation?: string;
}

const AlertsPanel = () => {
    const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
    const [newTicker, setNewTicker] = useState('');
    const [isChecking, setIsChecking] = useState(false);

    const BASE_URL = getApiBaseUrl();

    useEffect(() => {
        const saved = localStorage.getItem('terminal_watchlist');
        if (saved) {
            try {
                setWatchlist(JSON.parse(saved));
            } catch (e) {
                console.error("Failed to parse watchlist", e);
            }
        }
    }, []);

    useEffect(() => {
        localStorage.setItem('terminal_watchlist', JSON.stringify(watchlist));
    }, [watchlist]);

    const addTicker = async () => {
        const ticker = newTicker.trim().toUpperCase();
        if (!ticker || watchlist.some(item => item.ticker === ticker)) return;

        setNewTicker('');
        try {
            const res = await safeFetch(`${BASE_URL}/api/explain-chart?ticker=${ticker}`);
            if (!res.success) {
                if (res.isHtml) {
                    alert('AI Engine is currently waking up. Please try adding in 20 seconds.');
                    return;
                }
                throw new Error(res.error || 'Server returned invalid response.');
            }

            const data = res.data;
            
            const newItem: WatchlistItem = {
                ticker,
                lastPrice: data.signals?.price_change || 0,
                change: data.price_change,
                explanation: data.explanation
            };
            setWatchlist(prev => [newItem, ...prev]);
        } catch (e) {
            console.error("Failed to add ticker", e);
        }
    };

    const removeTicker = (ticker: string) => {
        setWatchlist(prev => prev.filter(item => item.ticker !== ticker));
    };

    return (
        <div className="alerts-container">
            <div className="alerts-header">
                <span className="grid-label">Market Watchlist & Alerts</span>
                <div className="add-ticker-box">
                    <input 
                        type="text" 
                        value={newTicker} 
                        onChange={(e) => setNewTicker(e.target.value)}
                        placeholder="ADD TICKER..."
                        onKeyDown={(e) => e.key === 'Enter' && addTicker()}
                    />
                    <button onClick={addTicker}>+</button>
                </div>
            </div>

            <div className="watchlist-grid">
                {watchlist.length === 0 && (
                    <div className="empty-watchlist">No active alerts. Add tickers to monitor institutional movement.</div>
                )}
                {watchlist.map((item) => (
                    <div key={item.ticker} className="watchlist-card">
                        <div className="watchlist-top">
                            <span className="item-ticker">{item.ticker}</span>
                            <span className={`item-change ${item.change >= 0 ? 'pos' : 'neg'}`}>
                                {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)}%
                            </span>
                            <button className="remove-btn" onClick={() => removeTicker(item.ticker)}>×</button>
                        </div>
                        <p className="item-explanation">{item.explanation}</p>
                    </div>
                ))}
            </div>

            <style jsx>{`
                .alerts-container {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                    padding: 20px;
                    background: var(--bg-surface);
                    border-top: 1px solid var(--border);
                }
                .alerts-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .add-ticker-box {
                    display: flex;
                    gap: 0;
                }
                .add-ticker-box input {
                    background: var(--bg-elevated);
                    border: 1px solid var(--border);
                    color: var(--text-primary);
                    padding: 4px 8px;
                    font-family: var(--font-mono);
                    font-size: 11px;
                    width: 100px;
                    outline: none;
                }
                .add-ticker-box button {
                    background: var(--primary);
                    color: white;
                    border: none;
                    padding: 0 10px;
                    cursor: pointer;
                    font-weight: bold;
                }
                .watchlist-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 12px;
                }
                .empty-watchlist {
                    grid-column: 1 / -1;
                    color: var(--text-muted);
                    font-size: 12px;
                    font-style: italic;
                    text-align: center;
                    padding: 20px;
                }
                .watchlist-card {
                    background: var(--bg-elevated);
                    border: 1px solid var(--border);
                    padding: 12px;
                    border-radius: 4px;
                }
                .watchlist-top {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }
                .item-ticker {
                    font-family: var(--font-mono);
                    font-weight: 700;
                    font-size: 14px;
                    color: var(--primary);
                }
                .item-change {
                    font-family: var(--font-mono);
                    font-weight: 700;
                    font-size: 13px;
                }
                .pos { color: #059669; }
                .neg { color: #dc2626; }
                .item-explanation {
                    font-size: 11px;
                    line-height: 1.4;
                    color: var(--text-muted);
                    margin: 0;
                }
                .remove-btn {
                    background: transparent;
                    border: none;
                    color: var(--text-muted);
                    cursor: pointer;
                    font-size: 16px;
                    padding: 0 4px;
                }
                .remove-btn:hover {
                    color: #ef4444;
                }
            `}</style>
        </div>
    );
};

export default AlertsPanel;
