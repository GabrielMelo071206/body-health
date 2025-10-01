// static/js/pix-generator.js - Gerador de código PIX dinâmico

/**
 * Gera código PIX baseado no valor do plano
 * @param {number} valor - Valor do plano em reais
 * @returns {string} - Código PIX formatado
 */
function gerarCodigoPix(valor) {
    // Chave PIX fixa
    const chavePix = "c0bfc211-5e37-45b7-8c75-29af72fd30bb";
    const beneficiario = "Lucas Marin Procopio";
    const cidade = "Sao Paulo";
    
    // Formatar valor com 2 casas decimais
    const valorFormatado = valor.toFixed(2);
    
    // Estrutura base do PIX EMV
    const payload = [
        "00020126",  // Payload Format Indicator
        "580014br.gov.bcb.pix",  // Merchant Account Information
        "0136" + chavePix,  // Chave PIX
        "5204",  // Merchant Category Code
        "0000",  // Código da categoria
        "5303",  // Transaction Currency
        "986",   // BRL (Real Brasileiro)
        "54" + String(valorFormatado.length).padStart(2, '0') + valorFormatado,  // Transaction Amount
        "5802BR",  // Country Code
        "59" + String(beneficiario.length).padStart(2, '0') + beneficiario,  // Merchant Name
        "60" + String(cidade.length).padStart(2, '0') + cidade,  // Merchant City
        "6229",  // Additional Data Field Template
        "0525" + gerarIdentificadorTransacao()  // Transaction ID
    ].join('');
    
    // Calcular CRC16
    const crc = calcularCRC16(payload + "6304");
    
    return payload + "6304" + crc;
}

/**
 * Gera identificador único para transação
 * @returns {string} - ID de transação
 */
function gerarIdentificadorTransacao() {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 15);
    return ("REC" + timestamp + random).substring(0, 25).toUpperCase();
}

/**
 * Calcula CRC16 para código PIX
 * @param {string} payload - String do payload PIX
 * @returns {string} - CRC16 em hexadecimal
 */
function calcularCRC16(payload) {
    const polinomio = 0x1021;
    let crc = 0xFFFF;
    
    for (let i = 0; i < payload.length; i++) {
        crc ^= (payload.charCodeAt(i) << 8);
        
        for (let j = 0; j < 8; j++) {
            if ((crc & 0x8000) !== 0) {
                crc = (crc << 1) ^ polinomio;
            } else {
                crc = crc << 1;
            }
        }
    }
    
    crc = crc & 0xFFFF;
    return crc.toString(16).toUpperCase().padStart(4, '0');
}

/**
 * Gera QR Code usando API externa
 * @param {string} pixCode - Código PIX
 * @returns {string} - URL da imagem QR Code
 */
function gerarUrlQRCode(pixCode) {
    // Usando API do QR Server (gratuita)
    const size = "250x250";
    const encodedPix = encodeURIComponent(pixCode);
    return `https://api.qrserver.com/v1/create-qr-code/?size=${size}&data=${encodedPix}`;
}

/**
 * Atualiza o PIX na página
 * @param {number} valor - Valor do plano
 */
function atualizarPix(valor) {
    try {
        // Gerar código PIX
        const codigoPix = gerarCodigoPix(valor);
        
        // Atualizar campo de texto
        const pixCodeInput = document.getElementById('pix-code');
        if (pixCodeInput) {
            pixCodeInput.value = codigoPix;
        }
        
        // Atualizar QR Code
        const qrCodeImg = document.getElementById('pix-qr-code');
        if (qrCodeImg) {
            qrCodeImg.src = gerarUrlQRCode(codigoPix);
            qrCodeImg.alt = `QR Code PIX - R$ ${valor.toFixed(2)}`;
        }
        
        console.log(`✅ PIX atualizado para R$ ${valor.toFixed(2)}`);
        console.log(`📱 Código: ${codigoPix.substring(0, 50)}...`);
        
    } catch (error) {
        console.error('❌ Erro ao gerar código PIX:', error);
    }
}

// Exportar funções
window.pixGenerator = {
    gerarCodigoPix,
    gerarUrlQRCode,
    atualizarPix
};