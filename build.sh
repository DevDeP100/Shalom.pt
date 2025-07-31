#!/bin/bash

# Script de build para Railway
echo "🚀 Iniciando build do projeto..."

# Criar diretório staticfiles se não existir
echo "📁 Criando diretório staticfiles..."
mkdir -p staticfiles

# Coletar arquivos estáticos
echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Executar migrações
echo "🗄️ Executando migrações..."
python manage.py migrate

echo "✅ Build concluído com sucesso!" 