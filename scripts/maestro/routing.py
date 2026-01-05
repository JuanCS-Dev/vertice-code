"""
Agent routing based on keywords and context.

Phase 10.3: Expanded Portuguese keyword coverage for all agents.
"""

import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text for accent-insensitive matching."""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn').lower()


def route_to_agent(prompt: str) -> str:
    """
    Intelligent routing based on keywords - Priority ordered to avoid conflicts.

    Phase 10.3: Bilingual EN/PT-BR support with imperative forms.
    """
    # Normalize for accent-insensitive matching
    p = normalize_text(prompt)

    # PRIORITY 1: Specific multi-word patterns (most specific first)
    testing_patterns = [
        # English
        'unit test', 'integration test', 'test case', 'write test', 'generate test',
        # Portuguese
        'teste unitario', 'teste de integracao', 'caso de teste',
        'cria teste', 'faz teste', 'roda os testes', 'executa teste',
    ]
    if any(w in p for w in testing_patterns):
        return 'testing'

    # Check for dockerfile BEFORE documentation
    if 'dockerfile' in p or 'docker file' in p:
        return 'devops'

    # Documentation patterns
    doc_patterns = [
        # English
        'write doc', 'api doc', 'docstring', 'readme', 'generate doc',
        # Portuguese
        'escreve doc', 'faz doc', 'documenta', 'gera doc', 'cria documentacao',
    ]
    if any(w in p for w in doc_patterns):
        return 'documentation'

    # PRIORITY 2: Domain-specific operations (high specificity)
    data_patterns = [
        # English
        'database', 'schema', 'query', 'sql', 'migration', 'table', 'index',
        'postgres', 'mysql', 'db', 'mongodb', 'redis',
        # Portuguese
        'banco de dados', 'tabela', 'consulta', 'migracao',
    ]
    if any(w in p for w in data_patterns):
        return 'data'

    devops_patterns = [
        # English
        'deploy', 'deployment', 'docker', 'container', 'kubernetes', 'k8s',
        'pod', 'helm', 'argocd', 'ci/cd', 'pipeline', 'terraform', 'iac',
        'infrastructure', 'incident', 'outage', 'monitor',
        # Portuguese
        'implanta', 'deploya', 'implantacao', 'incidente', 'infraestrutura',
        'faz deploy', 'faz o deploy', 'roda deploy',
    ]
    if any(w in p for w in devops_patterns):
        return 'devops'

    # PRIORITY 3: Code operations (medium specificity)
    review_patterns = [
        # English
        'review', 'audit', 'grade', 'lint', 'code review',
        # Portuguese
        'revisa', 'revise', 'revisao', 'analisa codigo', 'avalia codigo',
        'da uma olhada', 'checa o codigo',
    ]
    if any(w in p for w in review_patterns):
        return 'reviewer'

    refactor_patterns = [
        # English
        'refactor', 'rename', 'extract', 'inline', 'modernize', 'clean up',
        # Portuguese
        'refatora', 'renomeia', 'extrai', 'moderniza', 'limpa',
        'melhora o codigo', 'organiza o codigo', 'deixa mais limpo',
    ]
    if any(w in p for w in refactor_patterns):
        return 'refactorer'

    explore_patterns = [
        # English
        'explore', 'map', 'graph', 'blast radius', 'dependencies', 'structure',
        'find', 'search', 'locate', 'where', 'list', 'show',
        # Portuguese infinitive
        'explorar', 'encontrar', 'buscar', 'localizar', 'mostrar', 'listar',
        # Portuguese imperative
        'mostra', 'busca', 'encontra', 'acha', 'lista', 'procura',
        # Portuguese colloquial
        'onde', 'achar', 'onde esta', 'onde fica', 'me mostra', 'mostra ai',
        'como ta organizado', 'estrutura do projeto',
    ]
    if any(w in p for w in explore_patterns):
        return 'explorer'

    # PRIORITY 4: Design & Analysis (medium specificity)
    architect_patterns = [
        # English
        'architecture', 'system design', 'architect', 'uml', 'diagram', 'component',
        # Portuguese
        'arquitetura', 'design do sistema', 'arquiteto', 'diagrama', 'componente',
        'desenha arquitetura', 'projeta sistema',
    ]
    if any(w in p for w in architect_patterns):
        return 'architect'

    security_patterns = [
        # English
        'security', 'vulnerability', 'vulnerabilities', 'exploit', 'cve', 'owasp',
        'injection', 'xss', 'csrf', 'penetration', 'check for', 'find security',
        # Portuguese
        'seguranca', 'vulnerabilidade', 'ataque', 'brecha',
        'verifica seguranca', 'checa vulnerabilidade', 'analisa seguranca',
    ]
    if any(w in p for w in security_patterns):
        return 'security'

    performance_patterns = [
        # English
        'performance', 'bottleneck', 'profil', 'benchmark', 'slow', 'latency',
        'throughput', 'memory', 'optimize',
        # Portuguese
        'desempenho', 'lento', 'rapido', 'latencia', 'otimiza',
        'ta lento', 'demora', 'muito devagar', 'melhora performance',
    ]
    if any(w in p for w in performance_patterns):
        return 'performance'

    # PRIORITY 5: Planning (lower specificity - but NOT if deployment)
    planning_patterns = [
        # English
        'break down', 'strategy', 'roadmap', 'sop', 'how to',
        # Portuguese
        'passo a passo', 'estrategia', 'como fazer', 'como implementar',
        'faz um plano', 'planeja', 'planejamento',
    ]
    if any(w in p for w in planning_patterns):
        return 'planner'

    # Check plan (generic keyword - low priority)
    if ('plan' in p or 'plano' in p) and 'deploy' not in p:
        return 'planner'

    # PRIORITY 6: Catch-all single keywords (lowest priority - checked LAST)
    # Check test BEFORE security
    test_keywords = ['test', 'teste', 'testa', 'pytest']
    if any(w in p for w in test_keywords):
        return 'testing'

    # Check document AFTER architect
    doc_keywords = [
        'document', 'comment', 'explain',
        'documenta', 'comenta', 'explica', 'documentacao',
    ]
    if any(w in p for w in doc_keywords):
        return 'documentation'

    # PRIORITY 7: Bash/System commands (specific commands only)
    executor_keywords = [
        # File ops
        'ls', 'pwd', 'cd', 'mkdir', 'rm', 'cp', 'mv',
        # Process
        'ps', 'kill', 'top', 'htop',
        # Network
        'curl', 'wget', 'ping', 'netstat',
        # Git
        'git status', 'git diff', 'git log',
        # Generic execution
        'run', 'execute', 'command', 'bash', 'shell',
        # Portuguese
        'roda', 'executa', 'comando',
    ]
    if any(keyword in p for keyword in executor_keywords):
        return 'executor'

    # Default: Executor for everything else
    return 'executor'
