from django.contrib import admin

from .models import (
    User,
    Item,
    Pedido,
    ItemPedido,
    FormaPagamento,
    TransacaoMock,
    NotificacaoCozinha
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff'
    )
    search_fields = (
        'email',
        'username'
    )


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nome',
        'preco',
        'quantidade_estoque',
        'disponivel'
    )
    list_filter = (
        'disponivel',
    )
    search_fields = (
        'nome',
    )


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cliente',
        'status',
        'data_pedido'
    )

    list_filter = (
        'status',
    )

    inlines = [
        ItemPedidoInline
    ]


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nome',
        'ativo'
    )


@admin.register(TransacaoMock)
class TransacaoMockAdmin(admin.ModelAdmin):
    list_display = (
        'id_transacao',
        'pedido',
        'valor',
        'status',
        'criado_em'
    )

    list_filter = (
        'status',
    )


@admin.register(NotificacaoCozinha)
class NotificacaoCozinhaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'pedido',
        'lida',
        'criado_em'
    )

    list_filter = (
        'lida',
    )