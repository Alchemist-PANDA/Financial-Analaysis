import { NextResponse } from 'next/server';

export async function GET() {
  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ghouri112-financial-terminal-backend.hf.space';
  
  try {
    const res = await fetch(`${BACKEND_URL}/api/history`, {
      headers: {
        'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || 'dev_default_key'
      },
      cache: 'no-store'
    });
    
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
    return NextResponse.json([], { status: res.status });
  } catch (error) {
    return NextResponse.json([], { status: 500 });
  }
}
