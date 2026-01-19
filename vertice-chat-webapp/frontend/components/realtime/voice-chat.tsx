/**
 * Voice Chat Component with OpenAI Realtime API
 */
'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Mic, MicOff, Phone, PhoneOff, Settings } from 'lucide-react';
import { OpenAIRealtimeClient } from '@/lib/realtime/openai-client';
import { GeminiLiveClient } from '@/lib/realtime/gemini-client';

type VoiceProvider = 'openai' | 'gemini';

export function VoiceChat() {
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [provider, setProvider] = useState<VoiceProvider>('openai');
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const clientRef = useRef<OpenAIRealtimeClient | GeminiLiveClient | null>(null);

  const handleConnect = async () => {
    try {
      setConnectionStatus('connecting');

      if (provider === 'openai') {
        const apiKey = process.env.NEXT_PUBLIC_OPENAI_API_KEY!;
        if (!apiKey) throw new Error('OpenAI API key not configured');

        const client = new OpenAIRealtimeClient(apiKey);
        await client.connect();
        clientRef.current = client;
      } else {
        const apiKey = process.env.NEXT_PUBLIC_GOOGLE_API_KEY!;
        if (!apiKey) throw new Error('Google API key not configured');

        const client = new GeminiLiveClient(apiKey);
        await client.connect();
        clientRef.current = client;
      }

      setIsConnected(true);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Failed to connect to voice chat:', error);
      setConnectionStatus('error');
      alert(`Failed to connect: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDisconnect = () => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('disconnected');
  };

  const toggleMute = () => {
    // Mute functionality will be implemented with WebRTC track control
    setIsMuted(!isMuted);
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'error': return 'Connection Error';
      default: return 'Disconnected';
    }
  };

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (clientRef.current) {
        clientRef.current.disconnect();
      }
    };
  }, []);

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Phone className="h-5 w-5" />
              Voice Chat
            </CardTitle>
            <CardDescription>
              Real-time voice conversation with AI
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />
            <span className="text-sm font-medium">{getStatusText()}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Provider Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Voice Provider</label>
          <div className="flex gap-2">
            <Button
              variant={provider === 'openai' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setProvider('openai')}
              disabled={isConnected}
            >
              OpenAI Realtime
            </Button>
            <Button
              variant={provider === 'gemini' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setProvider('gemini')}
              disabled={isConnected}
            >
              Gemini Live
            </Button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex gap-2">
          {!isConnected ? (
            <Button
              onClick={handleConnect}
              className="flex-1"
              disabled={connectionStatus === 'connecting'}
            >
              {connectionStatus === 'connecting' ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Connecting...
                </>
              ) : (
                <>
                  <Phone className="mr-2 h-4 w-4" />
                  Connect
                </>
              )}
            </Button>
          ) : (
            <>
              <Button onClick={toggleMute} variant="outline" size="icon">
                {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>

              <Button onClick={handleDisconnect} variant="destructive" className="flex-1">
                <PhoneOff className="mr-2 h-4 w-4" />
                Disconnect
              </Button>
            </>
          )}
        </div>

        {/* Status Messages */}
        {isConnected && (
          <div className="text-sm text-muted-foreground">
            🎤 Speak naturally - the AI will respond in real-time
          </div>
        )}

        {connectionStatus === 'error' && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
            ⚠️ Connection failed. Check your API keys and network connection.
          </div>
        )}

        {/* Provider Info */}
        <div className="text-xs text-muted-foreground">
          {provider === 'openai' ? (
            <div>
              <Badge variant="secondary">OpenAI Realtime</Badge>
              <p className="mt-1">Uses GPT-4o Realtime API for low-latency voice chat</p>
            </div>
          ) : (
            <div>
              <Badge variant="secondary">Gemini Live</Badge>
              <p className="mt-1">Uses Gemini 2.0 Live API for multimodal conversations</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
