from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Categoria(models.Model):
    """Categoria dos eventos"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#007bff')

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nome


class Noticia(models.Model):
    """Modelo para notícias"""
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('publicado', 'Publicado'),
        ('arquivado', 'Arquivado'),
    ]

    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=300, blank=True)
    conteudo = models.TextField()
    resumo = models.TextField(max_length=500, blank=True, help_text='Resumo da notícia para exibição')
    imagem = models.ImageField(upload_to='noticias/', blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='noticias_criadas')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='noticias')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    em_destaque = models.BooleanField(default=False, help_text='Notícia em destaque na página inicial')
    data_publicacao = models.DateTimeField(default=timezone.now)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    visualizacoes = models.PositiveIntegerField(default=0)
    tags = models.CharField(max_length=500, blank=True, help_text='Tags separadas por vírgula')

    class Meta:
        verbose_name = 'Notícia'
        verbose_name_plural = 'Notícias'
        ordering = ['-data_publicacao']

    def __str__(self):
        return self.titulo

    @property
    def tempo_publicacao(self):
        """Retorna o tempo desde a publicação"""
        agora = timezone.now()
        diferenca = agora - self.data_publicacao

        if diferenca.days > 0:
            return f"{diferenca.days} dia(s) atrás"
        elif diferenca.seconds > 3600:
            horas = diferenca.seconds // 3600
            return f"{horas} hora(s) atrás"
        elif diferenca.seconds > 60:
            minutos = diferenca.seconds // 60
            return f"{minutos} minuto(s) atrás"
        else:
            return "Agora mesmo"

    @property
    def tags_list(self):
        """Retorna lista de tags"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []

    def incrementar_visualizacao(self):
        """Incrementa o contador de visualizações"""
        self.visualizacoes += 1
        self.save(update_fields=['visualizacoes'])


class Evento(models.Model):
    """Modelo para eventos"""
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('publicado', 'Publicado'),
        ('cancelado', 'Cancelado'),
        ('finalizado', 'Finalizado'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='eventos')
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    local = models.CharField(max_length=200)
    endereco = models.TextField()
    capacidade_maxima = models.PositiveIntegerField(default=0)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    imagem = models.ImageField(upload_to='eventos/', blank=True, null=True)
    link_externo = models.URLField(blank=True, null=True, help_text="Link para inscrição em site externo")
    usar_link_externo = models.BooleanField(default=False, help_text="Usar link externo em vez do sistema interno")
    em_destaque = models.BooleanField(default=False, help_text="Evento em destaque na página inicial")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    organizador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos_criados')

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-data_inicio']

    def __str__(self):
        return self.titulo

    @property
    def inscricoes_count(self):
        return self.inscricoes.filter(status='confirmada').count()

    @property
    def vagas_disponiveis(self):
        if self.capacidade_maxima == 0:
            return float('inf')
        return max(0, self.capacidade_maxima - self.inscricoes_count)

    @property
    def esta_cheio(self):
        return self.vagas_disponiveis == 0

    @property
    def esta_ativo(self):
        agora = timezone.now()
        return self.data_inicio <= agora <= self.data_fim

    @property
    def tem_link_externo(self):
        """Verifica se o evento tem link externo configurado"""
        return bool(self.usar_link_externo and self.link_externo)


class Inscricao(models.Model):
    """Modelo para inscrições em eventos"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='inscricoes')
    participante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscricoes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_inscricao = models.DateTimeField(auto_now_add=True)
    data_confirmacao = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    presente = models.BooleanField(default=False)
    data_presenca = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Inscrição'
        verbose_name_plural = 'Inscrições'
        unique_together = ['evento', 'participante']
        ordering = ['-data_inscricao']

    def __str__(self):
        return f"{self.participante.username} - {self.evento.titulo}"

    def confirmar(self):
        from django.utils import timezone
        self.status = 'confirmada'
        self.data_confirmacao = timezone.now()
        self.save()

    def cancelar(self):
        self.status = 'cancelada'
        self.save()

    def marcar_presenca(self):
        from django.utils import timezone
        self.presente = True
        self.status = 'presente'
        self.data_presenca = timezone.now()
        self.save()


class PerfilUsuario(models.Model):
    """Perfil estendido do usuário"""
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('N', 'Prefiro não informar'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefone = models.CharField(max_length=20, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True)
    nif = models.CharField(max_length=9, blank=True, null=True, unique=True, help_text='Número de Identificação Fiscal (9 dígitos)')
    endereco = models.TextField(blank=True, help_text='Rua, número e complemento')
    codigo_postal = models.CharField(max_length=8, blank=True, help_text='Código postal (formato: 0000-000)')
    cidade = models.CharField(max_length=100, blank=True)
    concelho = models.CharField(max_length=100, blank=True, help_text='Concelho/Município')
    distrito = models.CharField(max_length=100, blank=True, help_text='Distrito')
    foto = models.ImageField(upload_to='perfis/', blank=True, null=True)
    bio = models.TextField(blank=True)
    newsletter = models.BooleanField(default=True)
    email_verificado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuário'

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    @property
    def nome_completo(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}".strip()


class CodigoVerificacao(models.Model):
    """Código de verificação de email"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='codigos_verificacao')
    codigo = models.CharField(max_length=6, unique=True)
    email = models.EmailField()
    usado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()

    class Meta:
        verbose_name = 'Código de Verificação'
        verbose_name_plural = 'Códigos de Verificação'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Código para {self.email} - {self.codigo}"

    def gerar_codigo(self):
        """Gera um código de 6 dígitos"""
        import random
        self.codigo = str(random.randint(100000, 999999))
        self.save()

    def esta_valido(self):
        """Verifica se o código ainda é válido"""
        return not self.usado and timezone.now() <= self.expira_em

    def usar(self):
        """Marca o código como usado"""
        self.usado = True
        self.save()


class Certificado(models.Model):
    """Certificado de participação em eventos"""
    inscricao = models.OneToOneField(Inscricao, on_delete=models.CASCADE, related_name='certificado')
    codigo = models.CharField(max_length=50, unique=True)
    data_emissao = models.DateTimeField(auto_now_add=True)
    template = models.CharField(max_length=100, default='padrao')

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'

    def __str__(self):
        return f"Certificado - {self.inscricao.evento.titulo} - {self.inscricao.participante.username}"

    def gerar_codigo(self):
        import uuid
        self.codigo = str(uuid.uuid4()).replace('-', '')[:16].upper()
        self.save()


class Avaliacao(models.Model):
    """Avaliação do evento pelos participantes"""
    inscricao = models.OneToOneField(Inscricao, on_delete=models.CASCADE, related_name='avaliacao')
    nota = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True)
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        return f"Avaliação de {self.inscricao.participante.username} - {self.inscricao.evento.titulo}"
