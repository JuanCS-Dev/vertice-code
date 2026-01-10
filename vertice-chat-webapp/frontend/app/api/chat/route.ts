// Vertex AI Adapter (Custom Implementation)
// Securely bridges Next.js Edge Runtime to FastAPI Backend

export const runtime = 'edge';

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    // Extract Auth Token from incoming request
    const authHeader = req.headers.get('Authorization');

    // Call FastAPI Backend
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    const response = await fetch(`${backendUrl}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Pass the user's token if available, otherwise use dev-key for local testing
        'Authorization': authHeader || '',
        'X-API-Key': process.env.CLERK_SECRET_KEY || 'dev-key',
      },
      body: JSON.stringify({
        messages,
        model: 'gemini-2.5-pro',
        stream: true,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return new Response(errorText, { status: response.status });
    }

    // Pass-through the stream with correct headers
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'X-Vercel-AI-Data-Stream': 'v1',
      }
    });

  } catch (error: any) {
    console.error('Chat API Error:', error);
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
}
