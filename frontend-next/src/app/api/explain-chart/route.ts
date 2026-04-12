import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const ticker = searchParams.get('ticker');

  if (!ticker) {
    return NextResponse.json({ detail: 'Ticker is required' }, { status: 400 });
  }

  // Use the Python backend if possible, otherwise fallback to direct logic
  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ghouri112-financial-terminal-backend.hf.space';
  
  try {
    const res = await fetch(`${BACKEND_URL}/api/explain-chart?ticker=${ticker}`, {
      headers: {
        'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || 'dev_default_key'
      },
      next: { revalidate: 300 } // 5 minute cache
    });
    
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
    
    // Fallback: If HF Space is down, return a graceful message
    return NextResponse.json({
      ticker,
      price_change: 0,
      explanation: "Real-time analysis is currently being routed. If this persists, please ensure the backend engine is awake.",
      confidence: 0.5,
      signals: { news: null, volume: { volume_spike: false, ratio: 1.0 }, technical: null }
    });
  } catch (error) {
    return NextResponse.json({ detail: 'Backend connection error' }, { status: 500 });
  }
}
