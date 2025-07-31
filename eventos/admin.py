from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Evento, Inscricao, PerfilUsuario, Certificado, Avaliacao, CodigoVerificacao, Noticia


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cor_display', 'eventos_count']
    search_fields = ['nome']
    list_filter = ['nome']
    
    def cor_display(self, obj):
        return format_html(
            '<span style="color: {}; padding: 5px 10px; border-radius: 3px; background-color: {};">{}</span>',
            obj.cor, obj.cor, obj.cor
        )
    cor_display.short_description = 'Cor'
    
    def eventos_count(self, obj):
        return obj.eventos.count()
    eventos_count.short_description = 'Eventos'


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'categoria', 'status', 'em_destaque', 'data_publicacao', 'visualizacoes']
    list_filter = ['status', 'categoria', 'em_destaque', 'data_publicacao', 'autor']
    search_fields = ['titulo', 'subtitulo', 'conteudo', 'resumo']
    prepopulated_fields = {'resumo': ('titulo',)}
    readonly_fields = ['data_criacao', 'data_atualizacao', 'visualizacoes']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'subtitulo', 'autor', 'categoria')
        }),
        ('Conteúdo', {
            'fields': ('conteudo', 'resumo', 'tags')
        }),
        ('Configurações', {
            'fields': ('status', 'em_destaque', 'data_publicacao')
        }),
        ('Mídia', {
            'fields': ('imagem',)
        }),
        ('Estatísticas', {
            'fields': ('visualizacoes', 'data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('autor', 'categoria')


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'data_inicio', 'data_fim', 'status', 'capacidade_maxima', 'inscricoes_count', 'vagas_disponiveis', 'tem_link_externo', 'em_destaque']
    list_filter = ['status', 'categoria', 'data_inicio', 'organizador', 'usar_link_externo', 'em_destaque']
    search_fields = ['titulo', 'descricao', 'local']
    date_hierarchy = 'data_inicio'
    readonly_fields = ['criado_em', 'atualizado_em', 'inscricoes_count']
    filter_horizontal = []
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'descricao', 'categoria', 'organizador')
        }),
        ('Data e Local', {
            'fields': ('data_inicio', 'data_fim', 'local', 'endereco')
        }),
        ('Configurações', {
            'fields': ('capacidade_maxima', 'preco', 'status', 'em_destaque')
        }),
        ('Inscrição Externa', {
            'fields': ('usar_link_externo', 'link_externo'),
            'description': 'Configure se a inscrição será feita em site externo'
        }),
        ('Mídia', {
            'fields': ('imagem',)
        }),
        ('Informações do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def inscricoes_count(self, obj):
        return obj.inscricoes_count
    inscricoes_count.short_description = 'Inscrições'
    
    def vagas_disponiveis(self, obj):
        vagas = obj.vagas_disponiveis
        if vagas == float('inf'):
            return 'Ilimitado'
        return vagas
    vagas_disponiveis.short_description = 'Vagas Disponíveis'

    def tem_link_externo(self, obj):
        return bool(obj.tem_link_externo)
    tem_link_externo.boolean = True
    tem_link_externo.short_description = 'Link Externo'

    def em_destaque(self, obj):
        return obj.em_destaque
    em_destaque.boolean = True
    em_destaque.short_description = 'Em Destaque'


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ['participante', 'evento', 'status', 'data_inscricao', 'presente']
    list_filter = ['status', 'data_inscricao', 'presente', 'evento']
    search_fields = ['participante__username', 'participante__first_name', 'participante__last_name', 'evento__titulo']
    date_hierarchy = 'data_inscricao'
    readonly_fields = ['data_inscricao']
    
    fieldsets = (
        ('Informações da Inscrição', {
            'fields': ('evento', 'participante', 'status')
        }),
        ('Presença', {
            'fields': ('presente', 'data_presenca')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Datas', {
            'fields': ('data_inscricao', 'data_confirmacao'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirmar_inscricoes', 'cancelar_inscricoes', 'marcar_presenca']
    
    def confirmar_inscricoes(self, request, queryset):
        for inscricao in queryset:
            inscricao.confirmar()
        self.message_user(request, f"{queryset.count()} inscrições foram confirmadas.")
    confirmar_inscricoes.short_description = "Confirmar inscrições selecionadas"
    
    def cancelar_inscricoes(self, request, queryset):
        for inscricao in queryset:
            inscricao.cancelar()
        self.message_user(request, f"{queryset.count()} inscrições foram canceladas.")
    cancelar_inscricoes.short_description = "Cancelar inscrições selecionadas"
    
    def marcar_presenca(self, request, queryset):
        for inscricao in queryset:
            inscricao.marcar_presenca()
        self.message_user(request, f"{queryset.count()} presenças foram marcadas.")
    marcar_presenca.short_description = "Marcar presença das inscrições selecionadas"


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'nome_completo', 'telefone', 'cidade', 'concelho', 'newsletter']
    list_filter = ['genero', 'newsletter', 'criado_em', 'distrito']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'nif']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('usuario', 'telefone', 'data_nascimento', 'genero', 'nif')
        }),
        ('Endereço', {
            'fields': ('endereco', 'codigo_postal', 'cidade', 'concelho', 'distrito'),
            'description': 'Endereço no padrão português'
        }),
        ('Informações Adicionais', {
            'fields': ('foto', 'bio', 'newsletter', 'email_verificado')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def nome_completo(self, obj):
        return obj.nome_completo
    nome_completo.short_description = 'Nome Completo'


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ['inscricao', 'codigo', 'data_emissao', 'template']
    list_filter = ['data_emissao', 'template']
    search_fields = ['codigo', 'inscricao__participante__username', 'inscricao__evento__titulo']
    readonly_fields = ['data_emissao']
    
    actions = ['gerar_codigos']
    
    def gerar_codigos(self, request, queryset):
        for certificado in queryset:
            certificado.gerar_codigo()
        self.message_user(request, f"{queryset.count()} códigos foram gerados.")
    gerar_codigos.short_description = "Gerar códigos para certificados selecionados"


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['inscricao', 'nota', 'data_avaliacao']
    list_filter = ['nota', 'data_avaliacao']
    search_fields = ['inscricao__participante__username', 'inscricao__evento__titulo']
    readonly_fields = ['data_avaliacao']
    
    def nota_display(self, obj):
        return '⭐' * obj.nota
    nota_display.short_description = 'Nota'


@admin.register(CodigoVerificacao)
class CodigoVerificacaoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'email', 'codigo', 'usado', 'criado_em', 'expira_em', 'esta_valido']
    list_filter = ['usado', 'criado_em', 'expira_em']
    search_fields = ['usuario__username', 'email', 'codigo']
    readonly_fields = ['criado_em', 'codigo']
    
    def esta_valido(self, obj):
        return obj.esta_valido()
    esta_valido.boolean = True
    esta_valido.short_description = 'Válido'
