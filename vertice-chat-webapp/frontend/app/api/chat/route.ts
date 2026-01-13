/**
 * Vercel AI SDK Data Stream Protocol Bridge
 * 
 * Proxies chat requests to FastAPI backend and passes through
 * the streaming response in Vercel AI SDK Data Stream format.
 * 
 * REVISION: 2026-01-13-STREAM-PROTOCOL-FIX
 */

export const runtime = 'edge';

// Timeout for backend requests (2 minutes)
const BACKEND_TIMEOUT_MS = 120000;

export async function POST(req: Request) {
  const startTime = Date.now();

  try {
    const { messages } = await req.json();

    // Validate messages
    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return new Response(
        JSON.stringify({ error: 'Messages array is required and must not be empty' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Extract Auth Token from incoming request
    const authHeader = req.headers.get('Authorization');

    if (!authHeader) {
      console.warn('[Route] Missing Authorization header');
      return new Response(
        JSON.stringify({ error: 'Authentication required' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Backend URL from environment
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    console.log(`[Route] Proxying to: ${backendUrl}/api/v1/chat`);

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS);

    try {
      const response = await fetch(`${backendUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authHeader,
          'X-API-Key': process.env.CLERK_SECRET_KEY || 'internal',
        },
        body: JSON.stringify({
          messages,
          model: 'gemini-2.5-pro',
          stream: true,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[Route] Backend error ${response.status}: ${errorText}`);
        return new Response(
          JSON.stringify({ error: `Backend error: ${errorText}` }),
          { status: response.status, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Pass-through the stream with correct headers for Data Stream Protocol
      // CRITICAL: Content-Type must be text/plain for Vercel AI SDK
      return new Response(response.body, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'X-Vercel-AI-Data-Stream': 'v1',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'X-Response-Time': `${Date.now() - startTime}ms`,
        }
      });

    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      if (fetchError.name === 'AbortError') {
        console.error('[Route] Request timed out');
        return new Response(
          JSON.stringify({ error: 'Request timed out. Please try again.' }),
          { status: 504, headers: { 'Content-Type': 'application/json' } }
        );
      }

      throw fetchError;
    }

  } catch (error: any) {
    console.error('[Route] Chat API Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Internal server error',
        timestamp: new Date().toISOString()
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

