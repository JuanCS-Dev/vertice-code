/**
 * Edge Runtime API Route Example
 *
 * Runs on Vercel Edge Network for low latency globally
 *
 * Use cases:
 * - Authentication
 * - Simple data transformation
 * - Proxying to third-party APIs
 * - Lightweight computations
 *
 * Reference: https://nextjs.org/docs/app/building-your-application/rendering/edge-and-nodejs-runtimes
 */

// Opt into Edge Runtime
export const runtime = 'edge';

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Example: Simple validation and transformation
    const { message, timestamp } = body;

    if (!message) {
      return Response.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Transform data
    const transformedData = {
      originalMessage: message,
      processedAt: timestamp || new Date().toISOString(),
      edgeProcessed: true,
      region: request.headers.get('x-vercel-edge-region') || 'unknown',
    };

    return Response.json({
      success: true,
      data: transformedData,
    });

  } catch (error) {
    console.error('Edge API error:', error);

    return Response.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET() {
  // Health check endpoint
  return Response.json({
    status: 'ok',
    runtime: 'edge',
    timestamp: new Date().toISOString(),
  });
}