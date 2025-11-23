#!/usr/bin/env python3
"""
MASTERPIECE Shell Entry Point - OBRA PRIMA
"""

import os
import sys
import warnings

# Silence ALL gRPC/glog warnings BEFORE any imports
os.environ['GRPC_VERBOSITY'] = 'NONE'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')

# Redirect stderr to suppress C++ library warnings
_stderr_backup = sys.stderr
sys.stderr = open(os.devnull, 'w')

from qwen_dev_cli.cli.repl_masterpiece import start_masterpiece_repl

# Restore stderr
sys.stderr = _stderr_backup

if __name__ == "__main__":
    start_masterpiece_repl()
