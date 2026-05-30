# serializers.py
from rest_framework import serializers
from ..models import Item, Pedido, ItemPedido, FormaPagamento, TransacaoMock, NotificacaoCozinha

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class FormaPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPagamento
        fields = '__all__'

class ItemPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPedido
        fields = ['item', 'quantidade']
        # preco_unitario não deve ser enviado pelo usuário, o sistema pega automaticamente
        
class PedidoSerializer(serializers.ModelSerializer):
    # Serializer aninhado para receber os itens na hora de criar o pedido
    itens = ItemPedidoSerializer(many=True)
    total = serializers.SerializerMethodField()
    cliente_nome = serializers.CharField(source='cliente.get_full_name', read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'cliente', 'cliente_nome', 'status', 'data_pedido', 'itens', 'total']
        read_only_fields = ['status', 'data_pedido', 'cliente']

    def get_total(self, obj):
        return obj.get_total()

    def create(self, validated_data):
        itens_data = validated_data.pop('itens')
        
        # Pega o usuário logado que fez a requisição
        usuario = self.context['request'].user
        
        # Cria o pedido principal
        pedido = Pedido.objects.create(cliente=usuario, **validated_data)
        
        # Cria os itens do pedido e trava o preço no valor atual do cardápio
        for item_data in itens_data:
            item = item_data['item']
            quantidade = item_data['quantidade']
            preco_atual = item.preco 
            
            ItemPedido.objects.create(
                pedido=pedido, 
                item=item, 
                quantidade=quantidade,
                preco_unitario=preco_atual
            )
            
        return pedido

class NotificacaoCozinhaSerializer(serializers.ModelSerializer):
    pedido_id = serializers.IntegerField(source='pedido.id', read_only=True)
    
    class Meta:
        model = NotificacaoCozinha
        fields = ['id', 'pedido_id', 'lida', 'criado_em']