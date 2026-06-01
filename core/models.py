import uuid
import re
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core import validators, mail
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .manager import SoftDeleteManager, UserManager


# ==========================================
# USUÁRIOS E CLASSES BASE
# ==========================================

def get_sentinel_user():
    user, created = User.objects.get_or_create(
        email="deleted@example.com",
        defaults={"username": "deleted", "first_name": "Usuário", "last_name": "Deletado"}
    )
    return user

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        _('username'), max_length=15, unique=True, 
        help_text=_('Required. 15 characters or fewer. Letters, numbers and @/./+/-/_ characters'), 
        validators=[validators.RegexValidator(re.compile(r'^[\w.@+-]+$'), _('Enter a valid username.'), _('invalid'))]
    )    
    first_name = models.CharField(_('first name'), max_length=30)    
    last_name = models.CharField(_('last name'), max_length=30)    
    email = models.EmailField(_('email address'), max_length=255, unique=True)    
    is_staff = models.BooleanField(_('staff status'), default=False)    
    is_active = models.BooleanField(_('active'), default=True)
    # is_superuser removido: já é provido pelo PermissionsMixin
    
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    is_trusty = models.BooleanField(_('trusty'), default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
        
    def get_short_name(self) -> str:
        return self.first_name
        
    def email_user(self, subject, message, from_email=None) -> int:
        # CORREÇÃO: send_mail retorna int (quantidade de emails enviados)
        return mail.send_mail(subject, message, from_email, [self.email])


class UUIDModel(models.Model):
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True

class CreationTimestampedModel(models.Model):
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        User, verbose_name=_("Created by"), on_delete=models.SET(get_sentinel_user),
        null=True, editable=False, related_name="created_%(app_label)s_%(class)s_set",
    )
    class Meta:
        abstract = True

class UpdateTimestampedModel(models.Model):
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True, editable=False)
    updated_by = models.ForeignKey(
        User, verbose_name=_("Updated by"), on_delete=models.SET(get_sentinel_user),
        null=True, related_name="updated_%(app_label)s_%(class)s_set",
    )
    class Meta:
        abstract = True

class TimestampedModel(CreationTimestampedModel, UpdateTimestampedModel):
    class Meta:
        abstract = True

class BaseModel(UUIDModel, TimestampedModel):
    class Meta:
        abstract = True


# ==========================================
# CARDÁPIO
# ==========================================

class Item(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    quantidade_estoque = models.PositiveIntegerField(default=0)
    disponivel = models.BooleanField(default=True)

    class Meta:
        db_table = 'cardapio"."item'

    def __str__(self):
        return self.nome

class Pedido(models.Model):
    STATUS_PEDIDO = [
        ('CRIADO', 'Criado'),
        ('AGUARDANDO_PAGAMENTO', 'Aguardando Pagamento'),
        ('PREPARANDO', 'Preparando (Cozinha)'),
        ('CANCELADO', 'Cancelado'),
        ('CONCLUIDO', 'Concluído'),
    ]

    cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="pedidos"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_PEDIDO,
        default='CRIADO'
    )

    data_pedido = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pedidos"."pedido'

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.get_full_name()}"

    def get_total(self):
        return sum(item.subtotal() for item in self.itens.all())

# NOVA CLASSE: Para o pedido ter vários itens e salvar o preço na hora da compra
class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="itens"
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT
    )

    quantidade = models.PositiveIntegerField()

    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        db_table = 'pedidos"."item_pedido'

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def save(self, *args, **kwargs):
        if not self.pk:
            Item.objects.filter(
                id=self.item.id
            ).update(
                quantidade_estoque=models.F(
                    'quantidade_estoque'
                ) - self.quantidade
            )

        super().save(*args, **kwargs)

class FormaPagamento(models.Model):
    METODO_CHOICES = [
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('PIX', 'Pix'),
        ('BOLETO', 'Boleto'),
    ]

    nome = models.CharField(
        max_length=50,
        choices=METODO_CHOICES,
        unique=True
    )

    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'pagamento"."forma_pagamento'

    def __str__(self):
        return self.get_nome_display()

class TransacaoMock(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('APPROVED', 'Aprovado'),
        ('DECLINED', 'Recusado'),
        ('FAILED', 'Falhou'),
    ]

    id_transacao = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.PROTECT,
        related_name="pagamentos"
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    moeda = models.CharField(
        max_length=3,
        default='BRL'
    )

    forma_pagamento = models.ForeignKey(
        FormaPagamento,
        on_delete=models.PROTECT
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    mensagem_retorno = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pagamento"."transacao_mock'

# NOVA CLASSE: Para registrar que a cozinha foi notificada
class NotificacaoCozinha(models.Model):
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name="notificacao_cozinha"
    )

    lida = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificacao"."notificacao_cozinha'

