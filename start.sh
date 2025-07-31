#!/bin/bash

# Script de inicialização para Railway
echo "🚀 Iniciando aplicação..."

# Criar diretório staticfiles se não existir
echo "📁 Criando diretório staticfiles..."
mkdir -p staticfiles

# Coletar arquivos estáticos
echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Executar migrações
echo "🗄️ Executando migrações..."
python manage.py migrate

# Definir porta padrão se não estiver definida
PORT=${PORT:-8000}

# Iniciar o servidor
echo "🌐 Iniciando servidor na porta $PORT..."
exec gunicorn shalom_project.wsgi:application --bind 0.0.0.0:$PORT 