# seu_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import views

# O DefaultRouter cria as rotas automaticamente para os ViewSets
router = DefaultRouter()

# Registrando cada domínio na API
router.register(r'itens', views.ItemViewSet, basename='item')
router.register(r'formas-pagamento', views.FormaPagamentoViewSet, basename='formapagamento')
router.register(r'pedidos', views.PedidoViewSet, basename='pedido')
router.register(r'notificacoes', views.NotificacaoCozinhaViewSet, basename='notificacao')

urlpatterns = [
    # Inclui todas as rotas geradas pelo router
    path('', include(router.urls)),
]