// vertice-chat-webapp/frontend/components/voice/voice-input.tsx

'use client';

import { useState, useCallback } from 'react';
import { useVoiceRecording } from '@/lib/voice/use-voice-recording';
import { whisperClient } from '@/lib/voice/whisper-client';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Square, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceInputProps {
  onTranscription: (text: string) => void;
  onError: (error: string) => void;
  className?: string;
}

export function VoiceInput({ onTranscription, onError, className }: VoiceInputProps) {
  const { state, startRecording, stopRecording, cancelRecording } = useVoiceRecording();
  const [isTranscribing, setIsTranscribing] = useState(false);

  const handleStartRecording = useCallback(async () => {
    try {
      await startRecording();
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Failed to start recording');
    }
  }, [startRecording, onError]);

  const handleStopRecording = useCallback(async () => {
    try {
      const audioBlob = await stopRecording();
      setIsTranscribing(true);

      // Transcribe audio
      const transcription = await whisperClient.transcribe(audioBlob, {
        language: 'en', // TODO: Make configurable
        temperature: 0.2,
      });

      onTranscription(transcription);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Failed to transcribe audio');
    } finally {
      setIsTranscribing(false);
    }
  }, [stopRecording, onTranscription, onError]);

  const handleCancel = useCallback(() => {
    cancelRecording();
  }, [cancelRecording]);

  if (state.error) {
    return (
      <div className={cn("flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-md", className)}>
        <div className="text-destructive text-sm">
          Voice input error: {state.error}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.location.reload()}
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-3", className)}>
      {/* Recording State Indicator */}
      {state.isRecording && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span>Recording</span>
          </div>
          <span>{state.duration}s</span>
        </div>
      )}

      {state.isProcessing && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Processing...</span>
        </div>
      )}

      {isTranscribing && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Transcribing...</span>
        </div>
      )}

      {/* Control Buttons */}
      <div className="flex items-center gap-2">
        {!state.isRecording ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleStartRecording}
            disabled={state.isProcessing || isTranscribing}
            className="hover:bg-red-50 hover:border-red-200 hover:text-red-600"
          >
            <Mic className="w-4 h-4 mr-2" />
            Record
          </Button>
        ) : (
          <>
            <Button
              type="button"
              variant="default"
              size="sm"
              onClick={handleStopRecording}
              className="bg-red-600 hover:bg-red-700"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCancel}
            >
              <MicOff className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          </>
        )}
      </div>

      {/* Instructions */}
      {!state.isRecording && !state.isProcessing && !isTranscribing && (
        <div className="text-xs text-muted-foreground">
          Click "Record" to start voice input (requires microphone permission)
        </div>
      )}
    </div>
  );
}