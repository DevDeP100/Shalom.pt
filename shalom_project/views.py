from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def home_page(request):
    """Página principal do projeto"""
    return redirect('eventos:home')

def about_page(request):
    """Página sobre o projeto"""
    return render(request, 'about.html')

def contact_page(request):
    """Página de contato"""
    return render(request, 'contact.html') 