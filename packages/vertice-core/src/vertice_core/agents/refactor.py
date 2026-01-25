# Alias module for backward compatibility - use refactorer.py instead
from vertice_core.agents.refactorer import RefactorerAgent

# Explicit alias for tests expecting RefactorAgent (vs RefactorerAgent)
RefactorAgent = RefactorerAgent
