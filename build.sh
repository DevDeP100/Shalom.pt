#!/bin/bash

# Script de build para Railway
echo "🚀 Iniciando build do projeto..."

# Coletar arquivos estáticos
echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Executar migrações
echo "🗄️ Executando migrações..."
python manage.py migrate

echo "✅ Build concluído com sucesso!" 