// vertice-chat-webapp/frontend/components/commands/command-palette.tsx

'use client';

import { useState, useEffect, useRef } from 'react';
import { commandRegistry, CommandSuggestion } from '@/lib/commands';
import { useChatStore } from '@/lib/stores/chat-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Command, HelpCircle, Code, FileText, GitBranch, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';

const categoryIcons = {
  system: HelpCircle,
  code: Code,
  file: FileText,
  git: GitBranch,
  ai: Bot,
};

const categoryColors = {
  system: 'bg-blue-500',
  code: 'bg-green-500',
  file: 'bg-yellow-500',
  git: 'bg-purple-500',
  ai: 'bg-pink-500',
};

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onExecute: (command: string) => void;
  inputValue: string;
  onInputChange: (value: string) => void;
}

export function CommandPalette({
  isOpen,
  onClose,
  onExecute,
  inputValue,
  onInputChange,
}: CommandPaletteProps) {
  const [suggestions, setSuggestions] = useState<CommandSuggestion[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { currentSessionId } = useChatStore();

  // Update suggestions when input changes
  useEffect(() => {
    if (!inputValue.startsWith('/')) {
      setSuggestions([]);
      return;
    }

    const commandPart = inputValue.slice(1); // Remove the '/'
    const newSuggestions = commandRegistry.getSuggestions(commandPart);
    setSuggestions(newSuggestions);
    setSelectedIndex(0);
  }, [inputValue]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;

      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
        break;

      case 'Enter':
        e.preventDefault();
        if (suggestions[selectedIndex]) {
          const command = `/${suggestions[selectedIndex].command}`;
          onExecute(command);
          onClose();
        }
        break;

      case 'Escape':
        e.preventDefault();
        onClose();
        break;

      case 'Tab':
        e.preventDefault();
        if (suggestions[selectedIndex]) {
          const command = `/${suggestions[selectedIndex].command} `;
          onInputChange(command);
        }
        break;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 bg-popover border border-border rounded-lg shadow-lg z-50">
      {/* Input */}
      <div className="flex items-center gap-2 p-3 border-b border-border">
        <Command className="h-4 w-4 text-muted-foreground" />
        <Input
          ref={inputRef}
          value={inputValue}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a command..."
          className="border-0 shadow-none focus-visible:ring-0 px-0"
        />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <ScrollArea className="max-h-64">
          <div className="p-2">
            {suggestions.map((suggestion, index) => {
              const Icon = categoryIcons[suggestion.category];
              const isSelected = index === selectedIndex;

              return (
                <div
                  key={suggestion.command}
                  className={cn(
                    "flex items-center gap-3 p-2 rounded-md cursor-pointer hover:bg-accent",
                    isSelected && "bg-accent"
                  )}
                  onClick={() => {
                    onExecute(`/${suggestion.command}`);
                    onClose();
                  }}
                >
                  <div className={cn(
                    "flex items-center justify-center w-6 h-6 rounded",
                    categoryColors[suggestion.category]
                  )}>
                    <Icon className="h-3 w-3 text-white" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <code className="text-sm font-mono">/{suggestion.command}</code>
                      <Badge variant="secondary" className="text-xs">
                        {suggestion.category}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {suggestion.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      )}

      {/* Help text */}
      {inputValue.startsWith('/') && suggestions.length === 0 && (
        <div className="p-4 text-center text-muted-foreground">
          <p className="text-sm">No commands found. Type /help for available commands.</p>
        </div>
      )}

      {!inputValue.startsWith('/') && (
        <div className="p-4 text-center text-muted-foreground">
          <p className="text-sm">Type / to see available commands</p>
        </div>
      )}
    </div>
  );
}
