# Alias module for backward compatibility - use refactorer.py instead
from vertice_cli.agents.refactorer import *

# Explicit alias for tests expecting RefactorAgent (vs RefactorerAgent)
RefactorAgent = RefactorerAgent
