import { NextRequest, NextResponse } from 'next/server';

// AI Transparency Middleware - EU AI Act Compliance
export function aiTransparencyMiddleware(request: NextRequest) {
  const response = NextResponse.next();

  // Add EU AI Act required headers for AI-generated content
  response.headers.set('X-AI-Generated', 'true');
  response.headers.set('X-Model-Version', 'gemini-pro-2026');
  response.headers.set('X-Content-Provenance', 'ai-generated');
  response.headers.set('X-AI-Provider', 'Google Vertex AI');

  // Add C2PA-like content credentials header
  response.headers.set('Content-Credentials', JSON.stringify({
    '@context': 'https://contentcredentials.org/contexts/v1',
    'type': ['VerifiableCredential', 'ContentCredentials'],
    'issuer': 'https://vertice.ai',
    'issuanceDate': new Date().toISOString(),
    'credentialSubject': {
      'id': request.url,
      'contentType': 'ai-generated-text',
      'aiModel': 'gemini-pro-2026',
      'aiProvider': 'Google Vertex AI'
    }
  }));

  return response;
}