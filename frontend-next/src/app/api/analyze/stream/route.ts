import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const ticker = searchParams.get('ticker');
  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ghouri112-financial-terminal-backend.hf.space';

  // For SSE, we redirect to the actual backend directly to avoid Vercel timeout/proxy issues
  return NextResponse.redirect(`${BACKEND_URL}/api/analyze/stream?ticker=${ticker}`);
}
