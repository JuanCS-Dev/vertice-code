'use client';

import { useState } from 'react';
import { useCurrentSession, useChatStore } from '@/lib/stores/chat-store';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dropdown-menu';
import { Settings, Thermometer, FileText, Cpu } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const AVAILABLE_MODELS = [
  {
    id: 'claude-3-5-haiku-20241022',
    name: 'Claude Haiku',
    provider: 'Anthropic',
    description: 'Rápido e econômico',
    context: '200K tokens',
  },
  {
    id: 'claude-sonnet-4-5-20250901',
    name: 'Claude Sonnet',
    provider: 'Anthropic',
    description: 'Equilíbrio perfeito',
    context: '200K tokens',
  },
  {
    id: 'claude-opus-4-5-20251101',
    name: 'Claude Opus',
    provider: 'Anthropic',
    description: 'Máxima capacidade',
    context: '200K tokens',
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'OpenAI',
    description: 'Multimodal avançado',
    context: '128K tokens',
  },
  {
    id: 'gemini-pro',
    name: 'Gemini Pro',
    provider: 'Google',
    description: 'Multimodal Google',
    context: '1M tokens',
  },
];

export function ChatSettings() {
  const session = useCurrentSession();
  const { updateSessionSettings } = useChatStore();
  const [isOpen, setIsOpen] = useState(false);

  if (!session) return null;

  const handleModelChange = (modelId: string) => {
    updateSessionSettings(session.id, { model: modelId });
  };

  const handleTemperatureChange = (value: number[]) => {
    updateSessionSettings(session.id, { temperature: value[0] });
  };

  const handleMaxTokensChange = (value: number[]) => {
    updateSessionSettings(session.id, { maxTokens: value[0] });
  };

  const handleSystemPromptChange = (prompt: string) => {
    updateSessionSettings(session.id, { systemPrompt: prompt });
  };

  const selectedModel = AVAILABLE_MODELS.find(m => m.id === session.model) || AVAILABLE_MODELS[1];

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>

      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configurações da Conversa</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Model Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cpu className="h-4 w-4" />
                Modelo de IA
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Select value={session.model} onValueChange={handleModelChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AVAILABLE_MODELS.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        <div className="flex items-center justify-between w-full">
                          <div>
                            <div className="font-medium">{model.name}</div>
                            <div className="text-xs text-muted-foreground">
                              {model.provider} • {model.description}
                            </div>
                          </div>
                          <div className="text-xs text-muted-foreground ml-4">
                            {model.context}
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <div className="p-3 bg-muted rounded-lg">
                  <div className="text-sm font-medium">{selectedModel.name}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {selectedModel.description}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Temperature */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Thermometer className="h-4 w-4" />
                Criatividade (Temperature)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Mais Determinístico</Label>
                  <Label>Mais Criativo</Label>
                </div>
                <Slider
                  value={[session.settings.temperature]}
                  onValueChange={handleTemperatureChange}
                  min={0}
                  max={2}
                  step={0.1}
                  className="w-full"
                />
                <div className="text-center text-sm text-muted-foreground">
                  Valor atual: {session.settings.temperature}
                </div>
                <div className="text-xs text-muted-foreground">
                  Controla o quão criativa e imprevisível é a resposta.
                  Valores baixos (0.1-0.3) são mais focados e consistentes.
                  Valores altos (0.7-1.0) são mais criativos e diversos.
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Max Tokens */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Comprimento Máximo da Resposta
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Slider
                  value={[session.settings.maxTokens]}
                  onValueChange={handleMaxTokensChange}
                  min={256}
                  max={8192}
                  step={256}
                  className="w-full"
                />
                <div className="text-center text-sm text-muted-foreground">
                  {session.settings.maxTokens} tokens
                </div>
                <div className="text-xs text-muted-foreground">
                  Limite máximo de tokens na resposta.
                  1 token ≈ 4 caracteres em português.
                  Respostas mais longas custam mais.
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System Prompt */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Prompt do Sistema
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Textarea
                  value={session.settings.systemPrompt}
                  onChange={(e) => handleSystemPromptChange(e.target.value)}
                  placeholder="Digite instruções para o comportamento da IA..."
                  rows={4}
                />
                <div className="text-xs text-muted-foreground">
                  Instruções que definem como a IA deve se comportar nesta conversa.
                  Por exemplo: "Você é um assistente de programação Python especialista."
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}