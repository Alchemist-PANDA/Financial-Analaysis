import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const ticker = searchParams.get('ticker');

  if (!ticker) {
    return NextResponse.json({ detail: 'Ticker is required' }, { status: 400 });
  }

  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ghouri112-financial-terminal-backend.hf.space';
  
  try {
    const res = await fetch(`${BACKEND_URL}/api/timeline-markers?ticker=${ticker}`, {
      headers: {
        'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || 'dev_default_key'
      }
    });
    
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
    
    return NextResponse.json([]);
  } catch (error) {
    return NextResponse.json([]);
  }
}
