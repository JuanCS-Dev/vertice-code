'use client';

import { useState } from 'react';
import { useCurrentSession, useChatStore } from '@/lib/stores/chat-store';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Settings, Thermometer, FileText, Cpu, Github, Shield, Zap } from 'lucide-react';
import { GitHubConnect } from '../github/github-connect';
import { cn } from '@/lib/utils';

const AVAILABLE_MODELS = [
  {
    id: 'claude-3-5-sonnet',
    name: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    description: 'Fast, balanced, reliable.',
    isNew: false
  },
  {
    id: 'claude-opus-4-5',
    name: 'Claude 4.5 Opus',
    provider: 'Anthropic',
    description: 'Sovereign intelligence. Deep reasoning.',
    isNew: true
  },
  {
    id: 'gemini-3-pro',
    name: 'Gemini 3 Pro',
    provider: 'Google',
    description: '1M+ context window. Multi-modal.',
    isNew: true
  },
];

export function ChatSettings() {
  const session = useCurrentSession();
  const { updateSessionSettings } = useChatStore();
  const [isOpen, setIsOpen] = useState(false);

  if (!session) return (
    <Button variant="ghost" size="icon" className="text-zinc-600 hover:text-white transition-colors" disabled>
        <Settings className="h-4 w-4" />
    </Button>
  );

  const handleModelChange = (modelId: string) => {
    updateSessionSettings(session.id, { model: modelId });
  };

  const handleTemperatureChange = (value: number[]) => {
    updateSessionSettings(session.id, { temperature: value[0] });
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" className="text-zinc-600 hover:text-white transition-colors">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>

      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-[#0A0A0A] border-white/10 text-white font-sans selection:bg-primary/20 p-0 overflow-hidden">
        <DialogHeader className="p-6 border-b border-white/5 bg-[#080808]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg text-primary">
                <Settings className="h-5 w-5" />
            </div>
            <DialogTitle className="text-2xl font-bold tracking-tight">System Configuration</DialogTitle>
          </div>
        </DialogHeader>

        <div className="p-6 space-y-8">
          {/* Intelligence Matrix */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 text-zinc-500 uppercase tracking-widest text-[10px] font-bold">
                <Cpu className="h-3 w-3" /> Intelligence Matrix
            </div>
            
            <div className="grid grid-cols-1 gap-4">
                {AVAILABLE_MODELS.map((model) => (
                    <button
                        key={model.id}
                        onClick={() => handleModelChange(model.id)}
                        className={cn(
                            "flex items-center justify-between p-4 rounded-xl border transition-all text-left group",
                            session.model === model.id 
                                ? "bg-primary/5 border-primary/30" 
                                : "bg-white/[0.02] border-white/5 hover:border-white/10"
                        )}
                    >
                        <div className="flex items-center gap-4">
                            <div className={cn(
                                "w-10 h-10 rounded-lg flex items-center justify-center font-bold",
                                session.model === model.id ? "bg-primary text-black" : "bg-zinc-900 text-zinc-600 group-hover:text-zinc-400"
                            )}>
                                {model.name[0]}
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="font-bold text-sm">{model.name}</span>
                                    {model.isNew && <span className="bg-primary/20 text-primary text-[8px] font-bold px-1.5 py-0.5 rounded uppercase">New</span>}
                                </div>
                                <p className="text-[10px] text-zinc-500 mt-0.5">{model.description}</p>
                            </div>
                        </div>
                        {session.model === model.id && <Zap className="h-4 w-4 text-primary fill-primary" />}
                    </button>
                ))}
            </div>
          </section>

          {/* Core Harmonics */}
          <section className="space-y-6">
            <div className="flex items-center gap-2 text-zinc-500 uppercase tracking-widest text-[10px] font-bold">
                <Shield className="h-3 w-3" /> Core Harmonics
            </div>
            
            <div className="space-y-4 px-2">
                <div className="flex justify-between items-center">
                    <Label className="text-xs font-mono text-zinc-400">Entropy Level (Temperature)</Label>
                    <span className="text-xs font-mono text-primary">{session.settings.temperature}</span>
                </div>
                <Slider
                  value={[session.settings.temperature]}
                  onValueChange={handleTemperatureChange}
                  min={0}
                  max={1}
                  step={0.1}
                  className="w-full"
                />
                <div className="flex justify-between text-[9px] text-zinc-600 font-mono">
                    <span>DETERMINISTIC</span>
                    <span>CREATIVE</span>
                </div>
            </div>
          </section>

          <Separator className="bg-white/5" />

          {/* External Nodes */}
          <section className="space-y-4 pb-4">
            <div className="flex items-center gap-2 text-zinc-500 uppercase tracking-widest text-[10px] font-bold">
                <Github className="h-3 w-3" /> External Nodes
            </div>
            <GitHubConnect />
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
