#!/bin/bash
# Simplified Deployment for Current GCP Permissions
# Focuses on what we can deploy with current access

set -e

PROJECT_ID="${PROJECT_ID:-vertice-ai}"
REGION="${REGION:-us-central1}"

echo "🔧 DEPLOY SIMPLIFICADO - GCP ATUAL"
echo "=================================="
echo ""

echo "📊 STATUS ATUAL DO GCP:"
echo "- Projeto: $PROJECT_ID"
echo "- Permissões: Limitadas (sem billing admin)"
echo ""

echo "🎯 O QUE PODEMOS FAZER COM PERMISSÕES ATUAIS:"
echo "1. ✅ Configurar Firebase (se disponível)"
echo "2. ✅ Validar scripts sintaxe"
echo "3. ✅ Preparar arquivos de configuração"
echo "4. ❌ Deploy Cloud Run/GKE (precisa billing)"
echo ""

echo "🔍 VERIFICANDO O QUE ESTÁ DISPONÍVEL..."

# Check Firebase
echo ""
echo "🔥 FIREBASE STATUS:"
if command -v firebase &> /dev/null; then
    echo "✅ Firebase CLI instalado"
    firebase --version
else
    echo "❌ Firebase CLI não instalado"
fi

# Check project access
echo ""
echo "☁️ GCP PROJECT STATUS:"
if gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo "✅ Projeto $PROJECT_ID acessível"
else
    echo "❌ Projeto $PROJECT_ID não acessível"
fi

# Check billing
echo ""
echo "💰 BILLING STATUS:"
if gcloud billing projects describe $PROJECT_ID --format="value(billingAccountName)" 2>/dev/null | grep -q .; then
    echo "✅ Billing habilitado"
else
    echo "❌ Billing NÃO habilitado ou sem permissão"
fi

# Validate scripts
echo ""
echo "📋 VALIDAÇÃO DE SCRIPTS:"
scripts=("setup-multi-region-firebase.sh" "deploy-multi-region-vertex-ai.sh" "setup-observability.sh" "setup-zero-trust-security.sh" "optimize-ai-performance.sh")

for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        if bash -n "$script" 2>/dev/null; then
            echo "✅ $script - Sintaxe OK"
        else
            echo "❌ $script - Erro de sintaxe"
        fi
    else
        echo "❌ $script - Arquivo não encontrado"
    fi
done

echo ""
echo "🚀 PRÓXIMOS PASSOS RECOMENDADOS:"
echo "1. Configurar billing no GCP Console"
echo "2. Solicitar permissões de Owner/Admin no projeto"
echo "3. Executar: ./deploy-master.sh"
echo ""
echo "💡 ALTERNATIVA: Usar GCP Free Tier + Créditos ($300)"
echo ""
echo "⚠️ STATUS: Aguardando configuração GCP completa para deploy real"