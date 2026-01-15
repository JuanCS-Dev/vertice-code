#!/bin/bash
# Simplified Firebase Setup for Current Permissions
# Sets up basic Firebase configuration

set -e

PROJECT_ID="${PROJECT_ID:-vertice-ai}"

echo "🔥 FIREBASE SETUP SIMPLIFICADO"
echo "=============================="
echo ""

echo "📋 O QUE PODEMOS FAZER:"
echo "1. ✅ Configurar projeto Firebase"
echo "2. ✅ Inicializar Hosting básico"
echo "3. ❌ Criar backends (precisa upgrade do plano)"
echo ""

echo "🔧 EXECUTANDO CONFIGURAÇÃO BÁSICA..."

# Initialize Firebase if needed
if [ ! -f ".firebaserc" ]; then
    echo "📁 Inicializando Firebase project..."
    firebase init hosting --project $PROJECT_ID --yes
else
    echo "✅ Firebase já inicializado"
fi

# Check Firebase status
echo ""
echo "📊 STATUS FIREBASE:"
firebase projects:list
echo ""
firebase use --add
echo ""

echo "🎯 FIREBASE CONFIGURADO!"
echo ""
echo "📝 NOTA: Para backends multi-region, upgrade para Blaze plan necessário"
echo "💰 Custo estimado: ~$50/mês para Firebase Hosting"
echo ""
echo "🚀 PRÓXIMO: Configure billing e execute deploy completo"