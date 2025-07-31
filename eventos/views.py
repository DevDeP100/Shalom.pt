from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Evento, Inscricao, Categoria, PerfilUsuario, Avaliacao, CodigoVerificacao, Noticia
from .forms import RegistroUsuarioForm
from datetime import timedelta
import random


def home_page(request):
    """Página inicial inspirada no site da Comunidade Shalom Portugal"""
    # Eventos em destaque (marcados como em_destaque)
    eventos_destaque = Evento.objects.filter(
        status='publicado',
        em_destaque=True,
        data_inicio__gte=timezone.now()
    ).order_by('data_inicio')[:5]
    
    # Se não houver eventos em destaque, buscar os próximos eventos
    if not eventos_destaque:
        eventos_destaque = Evento.objects.filter(
            status='publicado',
            data_inicio__gte=timezone.now()
        ).order_by('data_inicio')[:5]
    
    # Eventos recentes
    eventos_recentes = Evento.objects.filter(
        status='publicado'
    ).order_by('-criado_em')[:6]
    
    # Notícias em destaque
    noticias_destaque = Noticia.objects.filter(
        status='publicado',
        em_destaque=True
    ).order_by('-data_publicacao')[:3]
    
    # Notícias recentes
    noticias_recentes = Noticia.objects.filter(
        status='publicado'
    ).order_by('-data_publicacao')[:6]
    
    # Combinar eventos e notícias em destaque para o carrossel
    carousel_items = []
    
    # Adicionar eventos em destaque
    for evento in eventos_destaque:
        carousel_items.append({
            'id': evento.id,
            'titulo': evento.titulo,
            'imagem': evento.imagem,
            'categoria': evento.categoria,
            'data_inicio': evento.data_inicio,
            'local': evento.local,
            'preco': evento.preco,
            'tipo': 'evento'
        })
    
    # Adicionar notícias em destaque
    for noticia in noticias_destaque:
        carousel_items.append({
            'id': noticia.id,
            'titulo': noticia.titulo,
            'imagem': noticia.imagem,
            'categoria': noticia.categoria,
            'data_publicacao': noticia.data_publicacao,
            'autor': noticia.autor,
            'visualizacoes': noticia.visualizacoes,
            'tipo': 'noticia'
        })
    
    # Ordenar por data (mais recentes primeiro)
    carousel_items.sort(key=lambda x: x.get('data_publicacao', x.get('data_inicio')), reverse=True)
    
    # Limitar a 5 itens no carrossel
    carousel_items = carousel_items[:5]
    
    # Categorias populares
    categorias = Categoria.objects.all()[:6]
    
    context = {
        'eventos_destaque': eventos_destaque,
        'eventos_recentes': eventos_recentes,
        'noticias_destaque': noticias_destaque,
        'noticias_recentes': noticias_recentes,
        'carousel_items': carousel_items,
        'categorias': categorias,
    }
    return render(request, 'eventos/home_shalom.html', context)


def login_usuario(request):
    """Login personalizado para usuários"""
    if request.user.is_authenticated:
        return redirect('eventos:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('eventos:home')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'eventos/login.html', {'form': form})


def logout_usuario(request):
    """Logout personalizado que redireciona para a página inicial"""
    logout(request)
    return redirect('eventos:home')


def registro_usuario(request):
    """Registro de novo usuário"""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Usuário inativo até verificar email
            user.save()
            
            # Criar perfil do usuário
            perfil = PerfilUsuario.objects.create(usuario=user)
            
            # Gerar código de verificação
            codigo = CodigoVerificacao.objects.create(
                usuario=user,
                email=user.email,
                expira_em=timezone.now() + timedelta(hours=24)
            )
            codigo.gerar_codigo()
            
            # Enviar email de verificação
            enviar_email_verificacao(user, codigo)
            
            messages.success(request, 'Conta criada com sucesso! Verifique seu email para ativar sua conta.')
            return redirect('eventos:verificar_email', user_id=user.id)
        else:
            # Se o formulário não for válido, mostrar erros
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'eventos/registro.html', {'form': form})


def verificar_email(request, user_id):
    """Página para verificar email"""
    user = get_object_or_404(User, id=user_id)
    codigo = CodigoVerificacao.objects.filter(
        usuario=user,
        usado=False,
        expira_em__gte=timezone.now()
    ).first()
    
    if request.method == 'POST':
        codigo_digitado = request.POST.get('codigo')
        if codigo and codigo.codigo == codigo_digitado:
            # Ativar usuário
            user.is_active = True
            user.save()
            
            # Marcar email como verificado
            perfil = user.perfil
            perfil.email_verificado = True
            perfil.save()
            
            # Marcar código como usado
            codigo.usar()
            
            # Fazer login do usuário
            login(request, user)
            
            messages.success(request, 'Email verificado com sucesso! Sua conta foi ativada.')
            return redirect('eventos:home')
        else:
            messages.error(request, 'Código inválido. Tente novamente.')
    
    return render(request, 'eventos/verificar_email.html', {'user': user})


def reenviar_codigo(request, user_id):
    """Reenviar código de verificação"""
    user = get_object_or_404(User, id=user_id)
    
    # Invalidar códigos anteriores
    CodigoVerificacao.objects.filter(usuario=user, usado=False).update(usado=True)
    
    # Criar novo código
    codigo = CodigoVerificacao.objects.create(
        usuario=user,
        email=user.email,
        expira_em=timezone.now() + timedelta(hours=24)
    )
    codigo.gerar_codigo()
    
    # Enviar email
    enviar_email_verificacao(user, codigo)
    
    messages.success(request, 'Novo código enviado para seu email!')
    return redirect('eventos:verificar_email', user_id=user.id)


def enviar_email_verificacao(user, codigo):
    """Enviar email de verificação"""
    subject = 'Verifique seu email - Comunidade Shalom Portugal'
    
    # Template HTML do email
    html_message = render_to_string('eventos/email_verificacao.html', {
        'user': user,
        'codigo': codigo,
        'site_name': 'Comunidade Shalom Portugal'
    })
    
    # Versão texto simples
    plain_message = strip_tags(html_message)
    
    # Enviar email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def login_inscricao(request):
    """Login específico para inscrições em eventos"""
    if request.user.is_authenticated:
        return redirect('eventos:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('eventos:home')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'eventos/login_inscricao.html', {'form': form})


def lista_eventos(request):
    """Lista todos os eventos publicados"""
    eventos = Evento.objects.filter(status='publicado').order_by('-data_inicio')
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        eventos = eventos.filter(categoria_id=categoria_id)
    
    busca = request.GET.get('busca')
    if busca:
        eventos = eventos.filter(
            Q(titulo__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(local__icontains=busca)
        )
    
    # Paginação
    paginator = Paginator(eventos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categorias = Categoria.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'busca': busca,
        'categoria_selecionada': categoria_id,
    }
    return render(request, 'eventos/lista_eventos.html', context)


def detalhe_evento(request, evento_id):
    """Detalhes de um evento específico"""
    evento = get_object_or_404(Evento, id=evento_id, status='publicado')
    inscricao_usuario = None
    
    if request.user.is_authenticated:
        inscricao_usuario = Inscricao.objects.filter(
            evento=evento, 
            participante=request.user
        ).first()
    
    context = {
        'evento': evento,
        'inscricao_usuario': inscricao_usuario,
    }
    return render(request, 'eventos/detalhe_evento.html', context)


@login_required
def inscrever_evento(request, evento_id):
    """Inscrever usuário em um evento"""
    evento = get_object_or_404(Evento, id=evento_id, status='publicado')
    
    # Verificar se email foi verificado
    if not request.user.perfil.email_verificado:
        messages.error(request, 'Você precisa verificar seu email antes de se inscrever em eventos.')
        return redirect('eventos:perfil_usuario')
    
    # Verificar se já está inscrito
    inscricao_existente = Inscricao.objects.filter(
        evento=evento, 
        participante=request.user
    ).first()
    
    if inscricao_existente:
        messages.warning(request, 'Você já está inscrito neste evento.')
        return redirect('eventos:detalhe_evento', evento_id=evento_id)
    
    # Verificar se o evento está cheio
    if evento.esta_cheio:
        messages.error(request, 'Este evento está lotado.')
        return redirect('eventos:detalhe_evento', evento_id=evento_id)
    
    # Criar inscrição
    inscricao = Inscricao.objects.create(
        evento=evento,
        participante=request.user,
        status='pendente'
    )
    
    messages.success(request, 'Inscrição realizada com sucesso!')
    return redirect('eventos:detalhe_evento', evento_id=evento_id)


@login_required
def cancelar_inscricao(request, evento_id):
    """Cancelar inscrição em um evento"""
    inscricao = get_object_or_404(
        Inscricao, 
        evento_id=evento_id, 
        participante=request.user
    )
    
    inscricao.cancelar()
    messages.success(request, 'Inscrição cancelada com sucesso!')
    return redirect('eventos:detalhe_evento', evento_id=evento_id)


@login_required
def meus_eventos(request):
    """Lista eventos do usuário logado"""
    inscricoes = Inscricao.objects.filter(participante=request.user).order_by('-data_inscricao')
    
    context = {
        'inscricoes': inscricoes,
    }
    return render(request, 'eventos/meus_eventos.html', context)


@login_required
def perfil_usuario(request):
    """Perfil do usuário logado"""
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        # Atualizar dados do usuário
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # Atualizar perfil
        perfil.telefone = request.POST.get('telefone', perfil.telefone)
        perfil.data_nascimento = request.POST.get('data_nascimento') or None
        perfil.genero = request.POST.get('genero', perfil.genero)
        perfil.nif = request.POST.get('nif', perfil.nif)
        perfil.endereco = request.POST.get('endereco', perfil.endereco)
        perfil.codigo_postal = request.POST.get('codigo_postal', perfil.codigo_postal)
        perfil.cidade = request.POST.get('cidade', perfil.cidade)
        perfil.concelho = request.POST.get('concelho', perfil.concelho)
        perfil.distrito = request.POST.get('distrito', perfil.distrito)
        perfil.bio = request.POST.get('bio', perfil.bio)
        perfil.newsletter = request.POST.get('newsletter') == 'on'
        perfil.save()
        
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('eventos:perfil_usuario')
    
    # Estatísticas do usuário
    inscricoes_count = Inscricao.objects.filter(participante=request.user).count()
    eventos_presente = Inscricao.objects.filter(participante=request.user, status='presente').count()
    
    context = {
        'perfil': perfil,
        'inscricoes_count': inscricoes_count,
        'eventos_presente': eventos_presente,
    }
    return render(request, 'eventos/perfil_usuario.html', context)


def api_eventos(request):
    """API para listar eventos (JSON)"""
    eventos = Evento.objects.filter(status='publicado').values(
        'id', 'titulo', 'descricao', 'data_inicio', 'data_fim', 
        'local', 'preco', 'capacidade_maxima'
    )
    
    return JsonResponse({'eventos': list(eventos)})


def lista_noticias(request):
    """Lista todas as notícias publicadas"""
    noticias = Noticia.objects.filter(status='publicado').order_by('-data_publicacao')
    
    # Notícias em destaque (primeiras 3 notícias)
    noticias_destaque = noticias[:3]
    
    # Paginação
    paginator = Paginator(noticias, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'noticias_destaque': noticias_destaque,
    }
    return render(request, 'eventos/lista_noticias.html', context)


def detalhe_noticia(request, noticia_id):
    """Detalhes de uma notícia específica"""
    noticia = get_object_or_404(Noticia, id=noticia_id, status='publicado')
    
    # Incrementar visualizações
    noticia.incrementar_visualizacao()
    
    # Notícias relacionadas
    noticias_relacionadas = Noticia.objects.filter(
        status='publicado',
        categoria=noticia.categoria
    ).exclude(id=noticia.id).order_by('-data_publicacao')[:3]
    
    context = {
        'noticia': noticia,
        'noticias_relacionadas': noticias_relacionadas,
    }
    return render(request, 'eventos/detalhe_noticia.html', context)


@login_required
def avaliar_evento(request, evento_id):
    """Avaliar um evento"""
    inscricao = get_object_or_404(
        Inscricao, 
        evento_id=evento_id, 
        participante=request.user,
        status='presente'
    )
    
    if request.method == 'POST':
        nota = request.POST.get('nota')
        comentario = request.POST.get('comentario', '')
        
        if nota:
            avaliacao, created = Avaliacao.objects.get_or_create(
                inscricao=inscricao,
                defaults={'nota': nota, 'comentario': comentario}
            )
            
            if not created:
                avaliacao.nota = nota
                avaliacao.comentario = comentario
                avaliacao.save()
            
            messages.success(request, 'Avaliação enviada com sucesso!')
            return redirect('meus_eventos')
    
    context = {
        'inscricao': inscricao,
    }
    return render(request, 'eventos/avaliar_evento.html', context)
