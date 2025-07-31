from django.urls import path
from . import views

app_name = 'eventos'

urlpatterns = [
    # Página inicial
    path('', views.home_page, name='home'),
    
    # Autenticação
    path('registro/', views.registro_usuario, name='registro'),
    path('verificar-email/<int:user_id>/', views.verificar_email, name='verificar_email'),
    path('reenviar-codigo/<int:user_id>/', views.reenviar_codigo, name='reenviar_codigo'),
    path('login/', views.login_usuario, name='login'),
    path('login-inscricao/', views.login_inscricao, name='login_inscricao'),
    path('logout/', views.logout_usuario, name='logout'),
    
    # Páginas públicas
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('evento/<int:evento_id>/', views.detalhe_evento, name='detalhe_evento'),
    path('noticias/', views.lista_noticias, name='lista_noticias'),
    path('noticia/<int:noticia_id>/', views.detalhe_noticia, name='detalhe_noticia'),
    path('api/eventos/', views.api_eventos, name='api_eventos'),
    
    # Páginas que requerem login
    path('inscrever/<int:evento_id>/', views.inscrever_evento, name='inscrever_evento'),
    path('cancelar/<int:evento_id>/', views.cancelar_inscricao, name='cancelar_inscricao'),
    path('meus-eventos/', views.meus_eventos, name='meus_eventos'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('avaliar/<int:evento_id>/', views.avaliar_evento, name='avaliar_evento'),
] 