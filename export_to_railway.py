#!/usr/bin/env python
"""
Script para exportar dados de eventos, categorias e notícias para a base de dados do Railway
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shalom_project.settings')
django.setup()

from django.db import connection
from eventos.models import Evento, Categoria, Noticia
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuração da base de dados do Railway
RAILWAY_DB_CONFIG = {
    'host': 'nozomi.proxy.rlwy.net',
    'port': 45954,
    'database': 'railway',
    'user': 'postgres',
    'password': 'iiWEtGHThaQxHFkNQXoJqUEbwxreDZwd'
}

def connect_to_railway_db():
    """Conectar à base de dados do Railway"""
    try:
        conn = psycopg2.connect(**RAILWAY_DB_CONFIG)
        print("✅ Conectado à base de dados do Railway")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar à base de dados do Railway: {e}")
        return None

def create_tables_if_not_exist(conn):
    """Criar tabelas se não existirem"""
    try:
        with conn.cursor() as cursor:
            # Criar tabela de categorias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eventos_categoria (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL UNIQUE,
                    descricao TEXT,
                    cor VARCHAR(7) DEFAULT '#007bff'
                );
            """)
            
            # Criar tabela de eventos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eventos_evento (
                    id SERIAL PRIMARY KEY,
                    titulo VARCHAR(200) NOT NULL,
                    descricao TEXT,
                    categoria_id INTEGER REFERENCES eventos_categoria(id),
                    data_inicio TIMESTAMP WITH TIME ZONE,
                    data_fim TIMESTAMP WITH TIME ZONE,
                    local VARCHAR(200),
                    endereco TEXT,
                    capacidade_maxima INTEGER DEFAULT 0,
                    preco DECIMAL(10,2) DEFAULT 0.00,
                    imagem VARCHAR(255),
                    link_externo VARCHAR(500),
                    usar_link_externo BOOLEAN DEFAULT FALSE,
                    em_destaque BOOLEAN DEFAULT FALSE,
                    status VARCHAR(20) DEFAULT 'rascunho',
                    organizador_id INTEGER,
                    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Criar tabela de notícias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eventos_noticia (
                    id SERIAL PRIMARY KEY,
                    titulo VARCHAR(200) NOT NULL,
                    subtitulo VARCHAR(300),
                    conteudo TEXT,
                    resumo TEXT,
                    imagem VARCHAR(255),
                    autor_id INTEGER,
                    categoria_id INTEGER REFERENCES eventos_categoria(id),
                    status VARCHAR(20) DEFAULT 'rascunho',
                    em_destaque BOOLEAN DEFAULT FALSE,
                    data_publicacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    data_criacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    visualizacoes INTEGER DEFAULT 0,
                    tags VARCHAR(500)
                );
            """)
            
        conn.commit()
        print("✅ Tabelas criadas/verificadas com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()

def export_categorias(conn):
    """Exportar categorias"""
    try:
        categorias = Categoria.objects.all()
        print(f"📦 Exportando {categorias.count()} categorias...")
        
        with conn.cursor() as cursor:
            for categoria in categorias:
                cursor.execute("""
                    INSERT INTO eventos_categoria (id, nome, descricao, cor)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        descricao = EXCLUDED.descricao,
                        cor = EXCLUDED.cor
                """, (
                    categoria.id,
                    categoria.nome,
                    categoria.descricao,
                    categoria.cor
                ))
        
        conn.commit()
        print("✅ Categorias exportadas com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao exportar categorias: {e}")
        conn.rollback()

def export_eventos(conn):
    """Exportar eventos"""
    try:
        eventos = Evento.objects.all()
        print(f"📦 Exportando {eventos.count()} eventos...")
        
        with conn.cursor() as cursor:
            for evento in eventos:
                cursor.execute("""
                    INSERT INTO eventos_evento (
                        id, titulo, descricao, categoria_id, data_inicio, data_fim, 
                        local, endereco, capacidade_maxima, preco, imagem, 
                        link_externo, usar_link_externo, em_destaque, status, 
                        organizador_id, criado_em, atualizado_em
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        titulo = EXCLUDED.titulo,
                        descricao = EXCLUDED.descricao,
                        categoria_id = EXCLUDED.categoria_id,
                        data_inicio = EXCLUDED.data_inicio,
                        data_fim = EXCLUDED.data_fim,
                        local = EXCLUDED.local,
                        endereco = EXCLUDED.endereco,
                        capacidade_maxima = EXCLUDED.capacidade_maxima,
                        preco = EXCLUDED.preco,
                        imagem = EXCLUDED.imagem,
                        link_externo = EXCLUDED.link_externo,
                        usar_link_externo = EXCLUDED.usar_link_externo,
                        em_destaque = EXCLUDED.em_destaque,
                        status = EXCLUDED.status,
                        organizador_id = EXCLUDED.organizador_id,
                        atualizado_em = CURRENT_TIMESTAMP
                """, (
                    evento.id,
                    evento.titulo,
                    evento.descricao,
                    evento.categoria.id if evento.categoria else None,
                    evento.data_inicio,
                    evento.data_fim,
                    evento.local,
                    evento.endereco,
                    evento.capacidade_maxima,
                    evento.preco,
                    evento.imagem.name if evento.imagem else None,
                    evento.link_externo,
                    evento.usar_link_externo,
                    evento.em_destaque,
                    evento.status,
                    evento.organizador.id if evento.organizador else None,
                    evento.criado_em,
                    evento.atualizado_em
                ))
        
        conn.commit()
        print("✅ Eventos exportados com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao exportar eventos: {e}")
        conn.rollback()

def export_noticias(conn):
    """Exportar notícias"""
    try:
        noticias = Noticia.objects.all()
        print(f"📦 Exportando {noticias.count()} notícias...")
        
        with conn.cursor() as cursor:
            for noticia in noticias:
                cursor.execute("""
                    INSERT INTO eventos_noticia (
                        id, titulo, subtitulo, conteudo, resumo, imagem, 
                        autor_id, categoria_id, status, em_destaque, 
                        data_publicacao, data_criacao, data_atualizacao, 
                        visualizacoes, tags
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        titulo = EXCLUDED.titulo,
                        subtitulo = EXCLUDED.subtitulo,
                        conteudo = EXCLUDED.conteudo,
                        resumo = EXCLUDED.resumo,
                        imagem = EXCLUDED.imagem,
                        autor_id = EXCLUDED.autor_id,
                        categoria_id = EXCLUDED.categoria_id,
                        status = EXCLUDED.status,
                        em_destaque = EXCLUDED.em_destaque,
                        data_publicacao = EXCLUDED.data_publicacao,
                        visualizacoes = EXCLUDED.visualizacoes,
                        tags = EXCLUDED.tags,
                        data_atualizacao = CURRENT_TIMESTAMP
                """, (
                    noticia.id,
                    noticia.titulo,
                    noticia.subtitulo,
                    noticia.conteudo,
                    noticia.resumo,
                    noticia.imagem.name if noticia.imagem else None,
                    noticia.autor.id if noticia.autor else None,
                    noticia.categoria.id if noticia.categoria else None,
                    noticia.status,
                    noticia.em_destaque,
                    noticia.data_publicacao,
                    noticia.data_criacao,
                    noticia.data_atualizacao,
                    noticia.visualizacoes,
                    noticia.tags
                ))
        
        conn.commit()
        print("✅ Notícias exportadas com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao exportar notícias: {e}")
        conn.rollback()

def main():
    """Função principal"""
    print("🚀 Iniciando exportação de dados para o Railway...")
    
    # Conectar à base de dados do Railway
    conn = connect_to_railway_db()
    if not conn:
        return
    
    try:
        # Criar tabelas se não existirem
        create_tables_if_not_exist(conn)
        
        # Exportar dados
        export_categorias(conn)
        export_eventos(conn)
        export_noticias(conn)
        
        print("🎉 Exportação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a exportação: {e}")
    
    finally:
        conn.close()
        print("🔌 Conexão com a base de dados fechada")

if __name__ == "__main__":
    main() 