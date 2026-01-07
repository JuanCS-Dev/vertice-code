#!/usr/bin/env python3
"""
Vertice MCP Python SDK - Practical Examples

Este arquivo demonstra como usar o SDK Vertice MCP Python
para interagir com o ecossistema de IA coletiva.

Generated with ❤️ by Vertex AI Codey
"""

import asyncio
from vertice_mcp import MCPClient, AsyncMCPClient, AgentTask, Skill
from vertice_mcp.types import MCPClientConfig


async def basic_usage_example():
    """Exemplo básico de uso do SDK."""
    print("🚀 Exemplo Básico: Conectando ao Ecossistema Vertice")
    print("-" * 50)

    # Configuração do cliente
    config = MCPClientConfig(
        endpoint="https://mcp.vertice.ai",  # Endpoint do servidor MCP
        api_key="your-api-key-here",  # Chave de API (opcional)
        timeout=30.0,  # Timeout em segundos
    )

    # Usando o cliente síncrono
    print("📡 Conectando ao servidor MCP...")
    client = MCPClient(config)

    try:
        with client:
            print("✅ Conexão estabelecida!")

            # Verificar status do servidor
            status = client.get_status()
            print(f"📊 Status do servidor: {status['status']}")
            print(f"🔢 Requests processados: {status['requests_processed']}")

            # Listar skills disponíveis
            skills = client.get_skills()
            print(f"🧠 Skills disponíveis: {len(skills)}")
            for skill in skills[:3]:  # Mostra os primeiros 3
                print(f"  • {skill.name}: {skill.description[:50]}...")

    except Exception as e:
        print(f"❌ Erro: {e}")

    print()


async def task_submission_example():
    """Exemplo de submissão de tarefas."""
    print("🎯 Exemplo: Submissão de Tarefas")
    print("-" * 50)

    client = MCPClient()

    # Criar uma tarefa
    task = AgentTask(
        id="example-task-001",
        description="""
        Analise este conjunto de dados de vendas e forneça insights sobre:
        1. Tendências de vendas por produto
        2. Padrões sazonais
        3. Recomendações para aumentar vendas
        """,
        agent_role="analyst",
        priority=2,
        metadata={
            "data_source": "sales_database",
            "time_range": "last_6_months",
            "output_format": "json",
        },
    )

    try:
        with client:
            print("📤 Enviando tarefa para o coletivo...")
            response = client.submit_task(task)

            print(f"✅ Tarefa aceita! ID: {response.task_id}")
            print(f"📊 Status: {response.status}")

            if response.estimated_completion:
                print(f"⏰ Conclusão estimada: {response.estimated_completion}")

            # Aguardar processamento (simulação)
            await asyncio.sleep(2)

            # Em produção, você verificaria o status periodicamente
            print("🔄 Em produção, você verificaria o status da tarefa aqui...")

    except Exception as e:
        print(f"❌ Erro ao submeter tarefa: {e}")

    print()


async def skill_management_example():
    """Exemplo de gerenciamento de skills."""
    print("🧠 Exemplo: Gerenciamento de Skills")
    print("-" * 50)

    client = MCPClient()

    # Aprender uma nova skill
    new_skill = Skill(
        name="sentiment_analysis",
        description="Análise de sentimento em texto usando técnicas avançadas de NLP",
        procedure_steps=[
            "Pré-processar o texto (limpeza, tokenização)",
            "Extrair features linguísticas (TF-IDF, embeddings)",
            "Aplicar modelo de classificação (BERT fine-tuned)",
            "Interpretar resultados e fornecer explicações",
        ],
        category="nlp",
        success_rate=0.94,
        usage_count=0,
        metadata={
            "model": "bert-base-multilingual",
            "languages": ["pt", "en", "es"],
            "accuracy": 0.94,
            "latency": "150ms",
        },
    )

    try:
        with client:
            print("🎓 Ensinando nova skill ao coletivo...")
            success = client.learn_skill(
                name=new_skill.name,
                description=new_skill.description,
                procedure_steps=new_skill.procedure_steps,
                category=new_skill.category,
            )

            if success:
                print("✅ Skill aprendida com sucesso!")
                print("📚 A skill agora está disponível para todo o coletivo.")
            else:
                print("❌ Falha ao aprender skill.")

            # Buscar uma skill específica
            print("\\n🔍 Buscando skill específica...")
            skill = client.get_skill("sentiment_analysis")

            if skill:
                print(f"✅ Skill encontrada: {skill.name}")
                print(f"📝 Descrição: {skill.description}")
                print(f"🎯 Taxa de sucesso: {skill.success_rate:.1%}")
                print(f"📊 Usos: {skill.usage_count}")
            else:
                print("❌ Skill não encontrada.")

            # Listar todas as skills disponíveis
            print("\\n📋 Listando todas as skills...")
            all_skills = client.get_skills()
            print(f"🧠 Total de skills disponíveis: {len(all_skills)}")

            # Agrupar por categoria
            categories = {}
            for skill in all_skills:
                if skill.category not in categories:
                    categories[skill.category] = []
                categories[skill.category].append(skill)

            print("📂 Skills por categoria:")
            for category, skills in categories.items():
                print(f"  • {category}: {len(skills)} skills")

    except Exception as e:
        print(f"❌ Erro no gerenciamento de skills: {e}")

    print()


async def async_operations_example():
    """Exemplo de operações assíncronas."""
    print("⚡ Exemplo: Operações Assíncronas")
    print("-" * 50)

    config = MCPClientConfig()
    async_client = AsyncMCPClient(config)

    try:
        async with async_client:
            print("🔄 Iniciando operações assíncronas...")

            # Executar múltiplas operações em paralelo
            tasks = []

            # Tarefa 1: Submeter tarefa
            task1 = AgentTask(
                id="async-task-1", description="Processar dados em lote", agent_role="processor"
            )
            tasks.append(async_client.submit_task(task1))

            # Tarefa 2: Buscar skills
            tasks.append(async_client.get_skills())

            # Tarefa 3: Verificar status
            tasks.append(async_client.get_status())

            # Aguardar todas as operações
            print("⏳ Executando operações em paralelo...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Processar resultados
            for i, result in enumerate(results, 1):
                if isinstance(result, Exception):
                    print(f"❌ Operação {i} falhou: {result}")
                else:
                    print(f"✅ Operação {i} concluída!")

                    if hasattr(result, "task_id"):  # É um AgentResponse
                        print(f"   📋 Task ID: {result.task_id}, Status: {result.status}")
                    elif isinstance(result, list):  # É lista de skills
                        print(f"   🧠 Skills encontradas: {len(result)}")
                    elif isinstance(result, dict):  # É status
                        print(f"   📊 Status: {result.get('status', 'unknown')}")

    except Exception as e:
        print(f"❌ Erro nas operações assíncronas: {e}")

    print()


async def error_handling_example():
    """Exemplo de tratamento de erros."""
    print("🛡️ Exemplo: Tratamento de Erros")
    print("-" * 50)

    client = MCPClient()

    # Exemplo 1: Endpoint inválido
    print("1️⃣ Testando endpoint inválido...")
    invalid_config = MCPClientConfig(endpoint="https://invalid-endpoint.com")
    invalid_client = MCPClient(invalid_config)

    try:
        with invalid_client:
            invalid_client.get_status()
    except Exception as e:
        print(f"✅ Erro tratado corretamente: {type(e).__name__}: {e}")

    # Exemplo 2: Skill inexistente
    print("\\n2️⃣ Testando skill inexistente...")
    try:
        with client:
            skill = client.get_skill("skill-que-nao-existe")
            if skill is None:
                print("✅ Skill inexistente retornou None corretamente")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

    # Exemplo 3: Rate limiting
    print("\\n3️⃣ Testando rate limiting...")
    try:
        with client:
            # Fazer muitas requisições rapidamente
            for i in range(10):
                client.get_status()
                await asyncio.sleep(0.1)  # Pequena pausa
    except Exception as e:
        print(f"✅ Rate limiting funcionou: {type(e).__name__}: {e}")

    print()


async def advanced_usage_example():
    """Exemplo de uso avançado."""
    print("🚀 Exemplo: Uso Avançado")
    print("-" * 50)

    client = MCPClient()

    try:
        with client:
            print("🔬 Explorando capacidades avançadas...")

            # 1. Analisar distribuição de skills por categoria
            skills = client.get_skills()

            # Agrupar por categoria e calcular estatísticas
            category_stats = {}
            for skill in skills:
                cat = skill.category
                if cat not in category_stats:
                    category_stats[cat] = {"count": 0, "avg_success_rate": 0.0, "total_usage": 0}

                category_stats[cat]["count"] += 1
                category_stats[cat]["avg_success_rate"] += skill.success_rate
                category_stats[cat]["total_usage"] += skill.usage_count

            # Calcular médias
            for cat, stats in category_stats.items():
                stats["avg_success_rate"] /= stats["count"]

            print("📊 Estatísticas por categoria:")
            for cat, stats in sorted(category_stats.items()):
                print(
                    f"  • {cat}: {stats['count']} skills, "
                    f"taxa média: {stats['avg_success_rate']:.1%}, "
                    f"usos totais: {stats['total_usage']}"
                )

            # 2. Encontrar skills mais eficazes
            if skills:
                best_skill = max(skills, key=lambda s: s.success_rate * s.usage_count)
                print(f"\\n🏆 Skill mais eficaz: {best_skill.name}")
                print(f"   Taxa de sucesso: {best_skill.success_rate:.1%}")
                print(f"   Usos: {best_skill.usage_count}")

            # 3. Demonstrar compartilhamento de skills
            print("\\n🤝 Compartilhando skill com o coletivo...")
            demo_skill = Skill(
                name="demo_collaboration_skill",
                description="Skill de demonstração para colaboração coletiva",
                procedure_steps=[
                    "Receber input do usuário",
                    "Processar com IA coletiva",
                    "Gerar resposta colaborativa",
                    "Aprender com feedback",
                ],
                category="collaboration",
                success_rate=0.89,
            )

            success = client.share_skill(demo_skill)
            if success:
                print("✅ Skill compartilhada com sucesso!")
                print("📢 Agora ela está disponível para todo o ecossistema.")
            else:
                print("❌ Falha ao compartilhar skill.")

    except Exception as e:
        print(f"❌ Erro no uso avançado: {e}")

    print()


async def main():
    """Função principal com menu de exemplos."""
    print("🌟 Vertice MCP Python SDK - Exemplos Práticos")
    print("=" * 60)
    print("🤖 Bem-vindo ao ecossistema de IA coletiva Vertice!")
    print("💝 Estes exemplos demonstram como usar o SDK Python")
    print("   para interagir com o coletivo de agentes inteligentes.")
    print("=" * 60)

    examples = {
        "1": ("Básico", basic_usage_example),
        "2": ("Tarefas", task_submission_example),
        "3": ("Skills", skill_management_example),
        "4": ("Assíncrono", async_operations_example),
        "5": ("Erros", error_handling_example),
        "6": ("Avançado", advanced_usage_example),
        "7": ("Todos", None),
    }

    while True:
        print("\\n📋 Exemplos disponíveis:")
        for key, (name, _) in examples.items():
            if key != "7":
                print(f"  {key}. {name}")
        print("  7. Executar todos os exemplos")
        print("  0. Sair")

        choice = input("\\nEscolha um exemplo (0-7): ").strip()

        if choice == "0":
            print("\\n👋 Até logo! Continue construindo IA coletiva! 🌟")
            break
        elif choice == "7":
            print("\\n🚀 Executando todos os exemplos...")
            for key, (name, func) in examples.items():
                if key != "7" and func:
                    print(f"\\n{'=' * 20} {name} {'=' * 20}")
                    await func()
        elif choice in examples and choice != "7":
            name, func = examples[choice]
            print(f"\\n{'=' * 20} {name} {'=' * 20}")
            await func()
        else:
            print("❌ Opção inválida. Tente novamente.")

        if choice != "7":
            input("\\nPressione Enter para continuar...")


if __name__ == "__main__":
    # Executar exemplos
    asyncio.run(main())
