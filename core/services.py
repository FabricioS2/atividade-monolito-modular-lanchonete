# services.py
from django.db import transaction
from .models import TransacaoMock, Pedido, NotificacaoCozinha

def processar_pagamento_e_notificar(transacao_id):
    """
    Processa o pagamento e, se aprovado, muda o status do pedido 
    e envia para a cozinha.
    """
    with transaction.atomic():
        transacao = TransacaoMock.objects.select_for_update().get(id_transacao=transacao_id)
        
        # Simulando a aprovação do pagamento
        transacao.status = 'APPROVED'
        transacao.save()
        
        # Regra Crítica: Se aprovou, manda pra cozinha
        if transacao.status == 'APPROVED':
            pedido = transacao.pedido
            
            if pedido.status != 'PREPARANDO':
                # Atualiza pedido
                pedido.status = 'PREPARANDO'
                pedido.save()
                
                # Notifica a cozinha
                NotificacaoCozinha.objects.create(pedido=pedido)
                
        return transacao