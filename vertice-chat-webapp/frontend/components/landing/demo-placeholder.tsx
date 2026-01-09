'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const DEMO_CODE = `
// The Vertice Difference: Divine Inspiration + AI Precision

async function generateSovereignCode() {
  const architect = new VerticeAgent({
    mode: 'sovereign',
    model: 'claude-opus-4.5',
    creativity: 'divine'
  });

  // Connecting to the collective consciousness...
  const insight = await architect.perceive(complexProblem);
  
  // Generating solution...
  return architect.manifest(insight);
}
`;

export function DemoPlaceholder() {
  const [text, setText] = useState('');
  
  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      setText(DEMO_CODE.slice(0, i));
      i++;
      if (i > DEMO_CODE.length) {
        clearInterval(interval);
      }
    }, 30); // Typing speed
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto mt-12 relative group cursor-pointer">
      <div className="absolute -inset-1 bg-gradient-to-r from-primary to-blue-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
      <div className="relative bg-[#080808] border border-border rounded-lg shadow-2xl overflow-hidden min-h-[400px]">
        {/* Fake Window Header */}
        <div className="h-8 bg-[#111111] border-b border-border flex items-center px-4 space-x-2">
          <div className="w-3 h-3 rounded-full bg-red-500/20"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500/20"></div>
          <div className="w-3 h-3 rounded-full bg-green-500/20"></div>
          <div className="ml-4 text-xs text-muted-foreground font-mono">vertice-tui — sovereign-mode</div>
        </div>
        
        {/* Video Placeholder Area */}
        <div className="p-6 font-mono text-sm md:text-base">
            <pre className="text-blue-300">
                {text}
                <span className="animate-pulse inline-block w-2 h-4 bg-primary align-middle ml-1"></span>
            </pre>
            
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="bg-black/50 backdrop-blur-sm border border-primary/30 px-6 py-3 rounded-full text-primary font-bold opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                    <span>▶</span> Watch the Demo
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
