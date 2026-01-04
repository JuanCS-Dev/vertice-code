"""Maestro V10 - Integrated Agent Orchestration Shell.

This module provides the main entry point for the Maestro orchestration system.
"""
import sys
import asyncio
from .orchestrator import Orchestrator
from .shell.core import Shell

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

__all__ = ['Orchestrator', 'Shell', 'main']

def main():
    """Main entry point for maestro."""
    try:
        shell = Shell()
        asyncio.run(shell.loop())
    except KeyboardInterrupt:
        print()
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

