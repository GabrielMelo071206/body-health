// static/js/pagamento.js - CRIAR ARQUIVO
class PagamentoValidator {
    constructor() {
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Máscara para cartão
        const numeroCartao = document.getElementById('numeroCartao');
        if (numeroCartao) {
            numeroCartao.addEventListener('input', this.formatarCartao);
        }
        
        // Máscara para validade
        const validade = document.getElementById('validade');
        if (validade) {
            validade.addEventListener('input', this.formatarValidade);
        }
        
        // Máscara para CVV
        const cvv = document.getElementById('cvv');
        if (cvv) {
            cvv.addEventListener('input', this.formatarCVV);
        }
        
        // Validação em tempo real
        const form = document.getElementById('card-payment-form');
        if (form) {
            form.addEventListener('submit', this.validarFormulario.bind(this));
        }
    }
    
    formatarCartao(e) {
        let valor = e.target.value.replace(/\D/g, '');
        valor = valor.replace(/(\d{4})(\d)/g, '$1 $2');
        valor = valor.replace(/(\d{4} \d{4})(\d)/g, '$1 $2');
        valor = valor.replace(/(\d{4} \d{4} \d{4})(\d)/g, '$1 $2');
        e.target.value = valor;
    }
    
    formatarValidade(e) {
        let valor = e.target.value.replace(/\D/g, '');
        valor = valor.replace(/(\d{2})(\d)/, '$1/$2');
        e.target.value = valor;
    }
    
    formatarCVV(e) {
        e.target.value = e.target.value.replace(/\D/g, '').substring(0, 4);
    }
    
    validarFormulario(e) {
        e.preventDefault();
        
        const numeroCartao = document.getElementById('numeroCartao').value.replace(/\s/g, '');
        const validade = document.getElementById('validade').value;
        const cvv = document.getElementById('cvv').value;
        const nomeCartao = document.getElementById('nomeCartao').value;
        
        let erros = [];
        
        // Validar número do cartão
        if (!this.validarNumeroCartao(numeroCartao)) {
            erros.push('Número do cartão inválido');
        }
        
        // Validar validade
        if (!this.validarValidade(validade)) {
            erros.push('Data de validade inválida');
        }
        
        // Validar CVV
        if (cvv.length < 3 || cvv.length > 4) {
            erros.push('CVV inválido');
        }
        
        // Validar nome
        if (nomeCartao.trim().length < 3) {
            erros.push('Nome no cartão é obrigatório');
        }
        
        if (erros.length > 0) {
            alert('Erros encontrados:\n' + erros.join('\n'));
            return false;
        }
        
        // Se chegou aqui, está tudo OK
        this.processarPagamento();
    }
    
    validarNumeroCartao(numero) {
        // Algoritmo de Luhn simplificado
        if (numero.length < 13 || numero.length > 19) return false;
        
        let soma = 0;
        let alternar = false;
        
        for (let i = numero.length - 1; i >= 0; i--) {
            let digito = parseInt(numero.charAt(i), 10);
            
            if (alternar) {
                digito *= 2;
                if (digito > 9) {
                    digito = (digito % 10) + 1;
                }
            }
            
            soma += digito;
            alternar = !alternar;
        }
        
        return (soma % 10) === 0;
    }
    
    validarValidade(validade) {
        if (!/^\d{2}\/\d{2}$/.test(validade)) return false;
        
        const [mes, ano] = validade.split('/');
        const mesNum = parseInt(mes, 10);
        const anoNum = parseInt('20' + ano, 10);
        
        if (mesNum < 1 || mesNum > 12) return false;
        
        const hoje = new Date();
        const dataValidade = new Date(anoNum, mesNum - 1);
        
        return dataValidade > hoje;
    }
    
    processarPagamento() {
        // Simular processamento
        const btnPagar = document.querySelector('#card-payment-form button[type="submit"]');
        btnPagar.disabled = true;
        btnPagar.innerHTML = '<i class="bi bi-hourglass-split"></i> Processando...';
        
        setTimeout(() => {
            alert('Pagamento processado com sucesso!\n(Esta é uma simulação)');
            btnPagar.disabled = false;
            btnPagar.innerHTML = '<i class="bi bi-check-lg"></i> Pagar com Cartão';
        }, 3000);
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    new PagamentoValidator();
});

// Função para copiar código PIX
function copyPixCode() {
    const pixCode = document.getElementById('pix-code');
    pixCode.select();
    document.execCommand('copy');
    alert('Código PIX copiado!');
}