'use client';

import { motion } from 'framer-motion';
import { Zap, Brain, Search, Shield, Save, AlertTriangle, CheckCircle2, Terminal } from 'lucide-react';
import { cn } from '@/lib/utils';

// -----------------------------------------------------------------------------
// SEMANTIC ICONS LIBRARY (2026)
// Alive, pulsing, and context-aware UI elements replacing static text tokens.
// -----------------------------------------------------------------------------

export const FlashAction = () => (
  <motion.span
    className="inline-flex items-center justify-center align-middle mx-1 px-1.5 py-0.5 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-[10px] font-bold tracking-wider uppercase select-none"
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
    whileHover={{ scale: 1.05, backgroundColor: "rgba(234, 179, 8, 0.2)" }}
  >
    <motion.span
      animate={{ opacity: [1, 0.5, 1] }}
      transition={{ duration: 1.5, repeat: Infinity }}
      className="mr-1.5"
    >
      <Zap className="w-3 h-3 fill-yellow-400" />
    </motion.span>
    EXEC
  </motion.span>
);

export const BrainProcess = () => (
  <motion.span
    className="inline-flex items-center justify-center align-middle mx-1 px-1.5 py-0.5 rounded-full bg-pink-500/10 border border-pink-500/20 text-pink-400 text-[10px] font-bold tracking-wider uppercase select-none"
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
  >
    <motion.span
      animate={{ rotate: [0, 5, -5, 0] }}
      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      className="mr-1.5"
    >
      <Brain className="w-3 h-3" />
    </motion.span>
    THINKING
  </motion.span>
);

export const SearchRadar = () => (
  <motion.span
    className="inline-flex items-center justify-center align-middle mx-1 px-1.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-bold tracking-wider uppercase select-none"
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
  >
    <motion.span
      animate={{ rotate: 360 }}
      transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
      className="mr-1.5 origin-center"
    >
      <Search className="w-3 h-3" />
    </motion.span>
    SEARCHING
  </motion.span>
);

export const SecurityShield = () => (
  <motion.span
    className="inline-flex items-center justify-center align-middle mx-1 px-1.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold tracking-wider uppercase select-none"
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
  >
    <Shield className="w-3 h-3 mr-1.5 fill-emerald-500/20" />
    SECURE
  </motion.span>
);

export const SaveDisk = () => (
  <motion.span
    className="inline-flex items-center justify-center align-middle mx-1 px-1.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-bold tracking-wider uppercase select-none"
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
  >
    <motion.span
      whileTap={{ y: 1 }}
      className="mr-1.5"
    >
      <Save className="w-3 h-3" />
    </motion.span>
    SAVED
  </motion.span>
);

export const WarningAlert = () => (
  <motion.span
    className="inline-flex items-center justify-center align-middle mx-1 px-1.5 py-0.5 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-[10px] font-bold tracking-wider uppercase select-none"
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
  >
    <motion.span
      animate={{ x: [-1, 1, -1] }}
      transition={{ duration: 0.2, repeat: 5 }}
      className="mr-1.5"
    >
      <AlertTriangle className="w-3 h-3" />
    </motion.span>
    WARNING
  </motion.span>
);

export const SuccessCheck = () => (
  <motion.span
    className="inline-flex items-center justify-center align-middle mx-1 px-1.5 py-0.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-[10px] font-bold tracking-wider uppercase select-none"
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
  >
    <motion.span
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 10 }}
      className="mr-1.5"
    >
      <CheckCircle2 className="w-3 h-3" />
    </motion.span>
    SUCCESS
  </motion.span>
);

export const TerminalCommand = () => (
  <motion.span
    className="inline-flex items-center justify-center align-middle mx-1 px-1.5 py-0.5 rounded-full bg-zinc-700/50 border border-zinc-600 text-zinc-300 text-[10px] font-mono tracking-tight select-none"
    initial={{ scale: 0.9, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
  >
    <Terminal className="w-3 h-3 mr-1.5" />
    CMD
  </motion.span>
);

// -----------------------------------------------------------------------------
// TOKEN MAP
// -----------------------------------------------------------------------------

export const SEMANTIC_TOKEN_MAP: Record<string, React.ComponentType> = {
  '⚡': FlashAction,
  '🧠': BrainProcess,
  '🔍': SearchRadar,
  '🛡️': SecurityShield,
  '💾': SaveDisk,
  '⚠️': WarningAlert,
  '✅': SuccessCheck,
  '💻': TerminalCommand
};
