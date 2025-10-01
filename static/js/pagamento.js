// static/js/pagamento.js - Script atualizado com geração PIX dinâmica

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== INICIALIZAR PIX COM VALOR INICIAL =====
    inicializarPixInicial();
    
    // ===== ALTERNÂNCIA ENTRE ABAS DE PAGAMENTO =====
    const tabButtons = document.querySelectorAll('.payment-tab-button');
    const tabContents = document.querySelectorAll('.payment-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const target = button.getAttribute('data-tab-target');
            
            // Remove active de todos
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Adiciona active no clicado
            button.classList.add('active');
            document.querySelector(target).classList.add('active');
        });
    });

    // ===== ATUALIZAR RESUMO E PIX AO TROCAR DE PLANO =====
    const planRadios = document.querySelectorAll('.plan-radio');
    
    planRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const nome = this.dataset.nome;
            const preco = parseFloat(this.dataset.preco);
            const duracao = parseInt(this.dataset.duracao);
            
            // Atualizar resumo do pedido
            atualizarResumo(nome, preco);
            
            // Atualizar código PIX
            if (window.pixGenerator) {
                window.pixGenerator.atualizarPix(preco);
            }
            
            console.log(`✅ Plano selecionado: ${nome} - R$ ${preco.toFixed(2)} por ${duracao} dias`);
        });
    });

    // ===== VALIDAÇÃO DO FORMULÁRIO DE CARTÃO =====
    const cardForm = document.getElementById('card-payment-form');
    
    if (cardForm) {
        cardForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!cardForm.checkValidity()) {
                e.stopPropagation();
                cardForm.classList.add('was-validated');
                return;
            }
            
            // Pegar plano selecionado
            const planoSelecionado = document.querySelector('.plan-radio:checked');
            const planoId = planoSelecionado ? planoSelecionado.value : null;
            const planoNome = planoSelecionado ? planoSelecionado.dataset.nome : 'Desconhecido';
            const planoPreco = planoSelecionado ? parseFloat(planoSelecionado.dataset.preco) : 0;
            
            // Simular processamento
            const submitBtn = cardForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processando pagamento...';
            
            setTimeout(() => {
                alert(`✅ Pagamento processado com sucesso!\n\nPlano: ${planoNome}\nValor: R$ ${planoPreco.toFixed(2)}\nID: ${planoId}`);
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
                
                // Aqui você faria a requisição real para o backend
                // window.location.href = '/pagamento/sucesso?plano_id=' + planoId;
            }, 2500);
        });
    }

    // ===== FORMATAÇÃO AUTOMÁTICA DE CAMPOS =====
    
    // Formatar número do cartão (adicionar espaços)
    const numeroCartao = document.getElementById('numeroCartao');
    if (numeroCartao) {
        numeroCartao.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s/g, '').replace(/\D/g, '');
            let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
            e.target.value = formattedValue.substring(0, 19); // Limitar a 16 dígitos + 3 espaços
        });
    }

    // Formatar validade (adicionar barra)
    const validade = document.getElementById('validade');
    if (validade) {
        validade.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
        });
    }

    // Formatar CVV (apenas números)
    const cvv = document.getElementById('cvv');
    if (cvv) {
        cvv.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 4);
        });
    }

    // Formatar CEP
    const cep = document.getElementById('cep');
    if (cep) {
        cep.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 5) {
                value = value.slice(0, 5) + '-' + value.slice(5, 8);
            }
            e.target.value = value;
        });
    }

    // ===== BOTÃO CONFIRMAR PAGAMENTO PIX =====
    const confirmPixBtn = document.getElementById('confirm-pix-payment');
    
    if (confirmPixBtn) {
        confirmPixBtn.addEventListener('click', function() {
            const planoSelecionado = document.querySelector('.plan-radio:checked');
            const planoId = planoSelecionado ? planoSelecionado.value : null;
            const planoNome = planoSelecionado ? planoSelecionado.dataset.nome : 'Desconhecido';
            const planoPreco = planoSelecionado ? parseFloat(planoSelecionado.dataset.preco) : 0;
            
            // Simular confirmação
            const originalText = this.textContent;
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verificando pagamento...';
            
            setTimeout(() => {
                alert(`✅ Pagamento PIX confirmado!\n\nPlano: ${planoNome}\nValor: R$ ${planoPreco.toFixed(2)}\nID: ${planoId}`);
                this.disabled = false;
                this.textContent = originalText;
                
                // Aqui você faria a requisição real para o backend
                // window.location.href = '/pagamento/sucesso?plano_id=' + planoId + '&metodo=pix';
            }, 2500);
        });
    }
});

// ===== FUNÇÃO PARA COPIAR CÓDIGO PIX =====
function copyPixCode() {
    const pixCode = document.getElementById('pix-code');
    
    if (pixCode) {
        pixCode.select();
        pixCode.setSelectionRange(0, 99999); // Para mobile
        
        navigator.clipboard.writeText(pixCode.value).then(() => {
            // Feedback visual no botão
            const copyBtn = document.querySelector('.pix-copy-btn-absolute');
            if (copyBtn) {
                const originalHTML = copyBtn.innerHTML;
                
                copyBtn.innerHTML = '<i class="bi bi-check-lg"></i>';
                copyBtn.style.backgroundColor = '#28a745';
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.style.backgroundColor = '';
                }, 2000);
            }
            
            // Mostrar toast de sucesso
            mostrarToast('✅ Código PIX copiado!', 'success');
            
        }).catch(err => {
            console.error('❌ Erro ao copiar: ', err);
            mostrarToast('❌ Erro ao copiar. Tente manualmente.', 'error');
        });
    }
}

// ===== FUNÇÃO AUXILIAR: ATUALIZAR RESUMO =====
function atualizarResumo(nome, preco) {
    const precoFormatado = preco.toLocaleString('pt-BR', { 
        style: 'currency', 
        currency: 'BRL' 
    });
    
    // Atualizar elementos do resumo
    const planoNomeEl = document.getElementById('plano-nome');
    const planoPrecoEl = document.getElementById('plano-preco');
    const totalPrecoEl = document.getElementById('total-preco');
    
    if (planoNomeEl) planoNomeEl.textContent = nome;
    if (planoPrecoEl) planoPrecoEl.textContent = precoFormatado;
    if (totalPrecoEl) totalPrecoEl.textContent = precoFormatado;
}

// ===== FUNÇÃO AUXILIAR: INICIALIZAR PIX =====
function inicializarPixInicial() {
    // Buscar plano selecionado inicialmente
    const planoInicial = document.querySelector('.plan-radio:checked');
    
    if (planoInicial && window.pixGenerator) {
        const preco = parseFloat(planoInicial.dataset.preco);
        window.pixGenerator.atualizarPix(preco);
        console.log('🎯 PIX inicializado com valor: R$', preco.toFixed(2));
    }
}

// ===== FUNÇÃO AUXILIAR: MOSTRAR TOAST =====
function mostrarToast(mensagem, tipo = 'info') {
    // Criar elemento de toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${tipo === 'success' ? 'success' : 'danger'} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.style.minWidth = '250px';
    toast.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Remover após 3 segundos
    setTimeout(() => {
        toast.remove();
    }, 3000);
}