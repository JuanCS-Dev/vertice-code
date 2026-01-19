/**
 * Voice Chat Page
 *
 * Dedicated page for real-time voice conversations with AI
 */
import { VoiceChat } from '@/components/realtime/voice-chat';

export default function VoiceChatPage() {
  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Voice Chat
          </h1>
          <p className="text-muted-foreground">
            Have natural conversations with AI using real-time voice
          </p>
        </div>

        <div className="flex justify-center">
          <VoiceChat />
        </div>

        <div className="mt-12 text-center text-sm text-muted-foreground">
          <p>
            🎤 Speak naturally • Supports OpenAI Realtime and Gemini Live APIs
          </p>
          <p className="mt-2">
            Real-time voice conversations with AI agents for coding assistance
          </p>
        </div>
      </div>
    </div>
  );
}
