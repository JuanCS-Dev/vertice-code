"""
ExplorerAgent: The Context Navigator

Busca REAL no filesystem usando ripgrep/glob.
Retorna arquivos relevantes organizados por estrutura do projeto.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from vertice_cli.agents.base import (
    AgentCapability,
    AgentRole,
    AgentTask,
    AgentResponse,
    BaseAgent,
)


class ExplorerAgent(BaseAgent):
    """Explorer Agent - Busca real no filesystem."""

    EXCLUDE_DIRS = {
        '__pycache__', '.git', 'node_modules', '.venv', 'venv', 'env',
        '.mypy_cache', '.pytest_cache', '.tox', 'dist', 'build', '.eggs',
        '.cache', '.idea', '.vscode', 'htmlcov', '.coverage', '.qwen',
        'egg-info', 'site-packages'
    }

    CODE_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.jsx', '.md', '.yaml', '.yml', '.json', '.toml', '.css', '.html'}

    def __init__(self, llm_client: Any, mcp_client: Any) -> None:
        super().__init__(
            role=AgentRole.EXPLORER,
            capabilities=[AgentCapability.READ_ONLY],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="Explorer Agent - Real filesystem search",
        )
        self._project_root = Path.cwd()

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Busca arquivos relevantes no projeto."""
        try:
            query = task.request.lower()
            max_files = task.context.get("max_files", 25)

            # Get project root from context files or cwd
            files_list = task.context.get("files", [])
            cwd = task.context.get("cwd", "")

            if files_list and files_list[0]:
                # Use parent of first file as project root
                first_file = Path(files_list[0])
                if first_file.exists():
                    # Go up to find a reasonable project root (has .git or pyproject.toml)
                    candidate = first_file.parent
                    while candidate != candidate.parent:
                        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
                            self._project_root = candidate
                            break
                        candidate = candidate.parent
                    else:
                        self._project_root = first_file.parent
                else:
                    self._project_root = Path(cwd) if cwd else Path.cwd()
            elif cwd:
                self._project_root = Path(cwd)

            # Detectar tipo de busca
            search_type = self._detect_search_type(query)

            found_files: List[Dict[str, Any]] = []

            # FIRST: Include files from context (always relevant)
            if files_list:
                for f in files_list:
                    if Path(f).exists():
                        found_files.append({
                            "path": str(Path(f).relative_to(self._project_root) if f.startswith(str(self._project_root)) else f),
                            "relevance": "HIGH",
                            "reason": "Arquivo fornecido no contexto"
                        })
                        # Also analyze content for classes/functions
                        try:
                            content = Path(f).read_text(errors='ignore')
                            # Extract class names
                            import re
                            classes = re.findall(r'class\s+(\w+)', content)
                            functions = re.findall(r'def\s+(\w+)', content)
                            if classes or functions:
                                found_files.append({
                                    "path": f,
                                    "relevance": "HIGH",
                                    "reason": f"Classes: {', '.join(classes[:5])}; Functions: {', '.join(functions[:10])}"
                                })
                        except Exception:
                            pass

            if search_type == "structure":
                # Usuário quer ver estrutura do projeto
                found_files.extend(self._get_project_structure())
            elif search_type == "directory":
                # Buscar diretório específico
                dir_name = self._extract_dir_name(query)
                found_files.extend(self._search_directory(dir_name))
            elif search_type == "deep_search":
                # Deep search for imports/usages
                keywords = self._extract_keywords(query)
                for kw in keywords[:1]: # Focus on main keyword
                     found_files.extend(self._deep_search_imports(kw))
            else:
                # Busca por keywords
                keywords = self._extract_keywords(query)

                # 1. Buscar em nomes de arquivos/diretórios (mais relevante)
                for kw in keywords:
                    found_files.extend(self._search_by_name(kw))

                # 2. Buscar conteúdo com ripgrep
                for kw in keywords[:3]:
                    found_files.extend(self._search_content(kw))

            # Deduplicar e ordenar
            seen = set()
            unique_files = []
            for f in found_files:
                path = f["path"]
                if path not in seen:
                    seen.add(path)
                    unique_files.append(f)

            # Ordenar: HIGH primeiro, depois por path
            unique_files.sort(key=lambda x: (0 if x["relevance"] == "HIGH" else 1, x["path"]))
            unique_files = unique_files[:max_files]

            # Construir resumo
            if unique_files:
                high = sum(1 for f in unique_files if f["relevance"] == "HIGH")
                summary = f"Encontrados {len(unique_files)} arquivos"
                if high:
                    summary += f" ({high} alta relevância)"
            else:
                summary = "Nenhum arquivo encontrado. Tente palavras-chave diferentes."

            return AgentResponse(
                success=True,
                data={
                    "relevant_files": unique_files,
                    "context_summary": summary,
                    "token_estimate": len(unique_files) * 200,
                },
                reasoning=summary,
            )

        except Exception as e:
            return AgentResponse(success=False, error=str(e), reasoning=f"Erro: {e}")

    def _detect_search_type(self, query: str) -> str:
        """Detecta o tipo de busca que o usuário quer."""
        structure_words = {'estrutura', 'structure', 'projeto', 'project', 'pastas', 'folders', 'organização'}
        dir_words = {'diretório', 'directory', 'pasta', 'folder', 'dir'}

        if any(w in query for w in structure_words):
            return "structure"
        if any(w in query for w in dir_words):
            return "directory"
        if "deep" in query or "import" in query or "usage" in query or "find" in query:
             return "deep_search"
        return "keyword"

    def _extract_dir_name(self, query: str) -> str:
        """Extrai nome de diretório da query."""
        # Palavras comuns a ignorar
        ignore = {'diretório', 'directory', 'pasta', 'folder', 'dir', 'onde', 'where', 'está', 'is', 'the', 'o', 'a'}
        words = query.split()
        for w in words:
            if w.lower() not in ignore and len(w) > 2:
                return w.lower()
        return ""

    def _extract_keywords(self, query: str) -> List[str]:
        """Extrai keywords relevantes da query."""
        stopwords = {
            'o', 'a', 'os', 'as', 'de', 'da', 'do', 'em', 'no', 'na', 'um', 'uma',
            'para', 'com', 'por', 'que', 'se', 'e', 'ou', 'onde', 'ficam', 'estão',
            'arquivos', 'files', 'where', 'are', 'my', 'the', 'is', 'meus', 'minha',
            'folder', 'pasta', 'diretório', 'directory', 'find', 'search', 'buscar',
            'procurar', 'localizar', 'show', 'mostrar', 'listar', 'list'
        }

        import re
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        # Manter ordem mas sem duplicatas
        seen = set()
        unique = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique.append(k)
        return unique[:8]

    def _get_project_structure(self) -> List[Dict[str, Any]]:
        """Retorna estrutura principal do projeto."""
        results = []

        # Arquivos raiz importantes
        root_files = ['README.md', 'pyproject.toml', 'setup.py', 'requirements.txt',
                      'Makefile', 'docker-compose.yml', '.env.example']
        for f in root_files:
            path = self._project_root / f
            if path.exists():
                results.append({
                    "path": f,
                    "relevance": "HIGH",
                    "reason": "Arquivo raiz do projeto"
                })

        # Diretórios principais (1 nível)
        for path in sorted(self._project_root.iterdir()):
            if path.is_dir() and path.name not in self.EXCLUDE_DIRS and not path.name.startswith('.'):
                # Contar arquivos no diretório
                try:
                    file_count = sum(1 for _ in path.glob('*.py'))
                    results.append({
                        "path": f"{path.name}/",
                        "relevance": "HIGH" if file_count > 0 else "MEDIUM",
                        "reason": f"Diretório com {file_count} arquivos .py"
                    })
                except (PermissionError, OSError):
                    pass

        return results

    def _search_directory(self, dir_name: str) -> List[Dict[str, Any]]:
        """Busca diretório e lista seu conteúdo."""
        results = []

        if not dir_name:
            return self._get_project_structure()

        # Encontrar diretórios que matcham
        for path in self._project_root.rglob(f"*{dir_name}*"):
            if path.is_dir() and not any(ex in str(path) for ex in self.EXCLUDE_DIRS):
                rel_path = str(path.relative_to(self._project_root))

                # Adicionar o diretório
                results.append({
                    "path": f"{rel_path}/",
                    "relevance": "HIGH",
                    "reason": f"Diretório matching '{dir_name}'"
                })

                # Listar arquivos dentro
                try:
                    for f in sorted(path.iterdir())[:15]:
                        if f.is_file() and f.suffix in self.CODE_EXTENSIONS:
                            results.append({
                                "path": str(f.relative_to(self._project_root)),
                                "relevance": "MEDIUM",
                                "reason": f"Arquivo em {rel_path}/"
                            })
                except (PermissionError, OSError):
                    pass

        return results[:30]

    def _search_by_name(self, keyword: str) -> List[Dict[str, Any]]:
        """Busca arquivos/diretórios pelo nome."""
        results = []

        try:
            # Buscar diretórios
            for path in self._project_root.rglob(f"*{keyword}*"):
                if any(ex in str(path) for ex in self.EXCLUDE_DIRS):
                    continue

                rel_path = str(path.relative_to(self._project_root))

                if path.is_dir():
                    results.append({
                        "path": f"{rel_path}/",
                        "relevance": "HIGH",
                        "reason": f"Diretório contém '{keyword}'"
                    })
                    # Listar alguns arquivos do diretório
                    try:
                        for f in list(path.iterdir())[:5]:
                            if f.is_file() and f.suffix in self.CODE_EXTENSIONS:
                                results.append({
                                    "path": str(f.relative_to(self._project_root)),
                                    "relevance": "MEDIUM",
                                    "reason": f"Em diretório '{keyword}'"
                                })
                    except (PermissionError, OSError):
                        pass

                elif path.is_file() and path.suffix in self.CODE_EXTENSIONS:
                    results.append({
                        "path": rel_path,
                        "relevance": "HIGH",
                        "reason": f"Nome contém '{keyword}'"
                    })
        except Exception:
            pass

        return results

    def _search_content(self, keyword: str) -> List[Dict[str, Any]]:
        """Busca keyword no conteúdo dos arquivos usando ripgrep."""
        results = []

        try:
            # Construir comando ripgrep
            exclude_args = []
            for ex in self.EXCLUDE_DIRS:
                exclude_args.extend(['-g', f'!{ex}/**'])

            cmd = ['rg', '-l', '-i', '--max-count=1'] + exclude_args + [keyword, str(self._project_root)]

            output = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if output.stdout:
                for line in output.stdout.strip().split('\n')[:20]:
                    if line:
                        try:
                            rel_path = str(Path(line).relative_to(self._project_root))
                            # Não duplicar se já foi encontrado por nome
                            results.append({
                                "path": rel_path,
                                "relevance": "MEDIUM",
                                "reason": f"Contém '{keyword}'"
                            })
                        except (ValueError, OSError):
                            pass

        except FileNotFoundError:
            # ripgrep não instalado, usar grep
            try:
                cmd = ['grep', '-rl', '-i', '--include=*.py', keyword, str(self._project_root)]
                output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if output.stdout:
                    for line in output.stdout.strip().split('\n')[:15]:
                        if line and not any(ex in line for ex in self.EXCLUDE_DIRS):
                            try:
                                rel_path = str(Path(line).relative_to(self._project_root))
                                results.append({
                                    "path": rel_path,
                                    "relevance": "MEDIUM",
                                    "reason": f"Contém '{keyword}'"
                                })
                            except (ValueError, OSError):
                                pass
            except (subprocess.TimeoutExpired, OSError):
                pass
        except (subprocess.TimeoutExpired, OSError):
            pass

        return results

    def _deep_search_imports(self, keyword: str) -> List[Dict[str, Any]]:
        """Deep search for imports and usages recursively."""
        results = []
        try:
             # Use grep to find 'import ... keyword' or 'from ... keyword'
             # Or usages like 'keyword('
             cmd = ['grep', '-r', '-l', '-E', fr"import.*{keyword}|from.*{keyword}|{keyword}\(", str(self._project_root)]
             
             # Exclude dirs
             exclude_args = []
             for ex in self.EXCLUDE_DIRS:
                exclude_args.extend(['--exclude-dir', ex])
             
             cmd.extend(exclude_args)
             
             output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
             
             if output.stdout:
                 for line in output.stdout.strip().split('\n')[:30]:
                     if line:
                         try:
                             rel_path = str(Path(line).relative_to(self._project_root))
                             results.append({
                                 "path": rel_path,
                                 "relevance": "HIGH",
                                 "reason": f"Deep usage/import of '{keyword}'"
                             })
                         except Exception:
                             pass
        except Exception as e:
            print(f"Deep search failed: {e}")
            
        return results
