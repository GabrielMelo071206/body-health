document.addEventListener("DOMContentLoaded", function () {
  const tipoContaSelect = document.getElementById("tipoConta");
  const camposCliente = document.getElementById("camposCliente");
  const camposProfissional = document.getElementById("camposProfissional");

  tipoContaSelect.addEventListener("change", function () {
    const tipo = this.value;
    camposCliente.style.display = tipo === "cliente" ? "block" : "none";
    camposProfissional.style.display = tipo === "profissional" ? "block" : "none";
  });

  // Esconde os campos inicialmente
  camposCliente.style.display = "none";
  camposProfissional.style.display = "none";
});

    const textos = {
      termos: `<h3>📄 Termos de Serviço — Body Healthy</h3>
        <p>Última atualização: 06/08/2025</p>
        <p>Seja bem-vindo à Body Healthy! Ao acessar ou utilizar nossos serviços, você concorda com os seguintes Termos de Serviço...</p>
        <ol>
          <li><strong>Aceitação dos Termos</strong> – Ao acessar ou utilizar qualquer parte do site, você concorda com estes termos.</li>
          <li><strong>Descrição do Serviço</strong> – Oferecemos planos, artigos e consultorias online.</li>
          <li><strong>Cadastro</strong> – Você deve fornecer informações verdadeiras e manter sua conta segura.</li>
          <li><strong>Conduta</strong> – Proibido conteúdo ofensivo, invasão de sistemas etc.</li>
          <li><strong>Conteúdo</strong> – Reservamos o direito de remover conteúdos inadequados.</li>
          <li><strong>Direitos Autorais</strong> – Nada pode ser copiado sem autorização.</li>
          <li><strong>Responsabilidade</strong> – Não substituímos orientação médica profissional.</li>
          <li><strong>Modificações</strong> – Os termos podem ser atualizados sem aviso prévio.</li>
          <li><strong>Cancelamento</strong> – Contas podem ser encerradas a pedido do usuário ou por violação.</li>
          <li><strong>Contato</strong> – contato@bodyhealthy.com.br</li>
        </ol>`,
      privacidade: `<h3>📄 Política de Privacidade — Body Healthy</h3>
        <p>Última atualização: 06/08/2025</p>
        <ol>
          <li><strong>Coleta de Dados</strong> – Nome, e-mail, CPF, entre outros.</li>
          <li><strong>Uso</strong> – Para personalizar sua experiência, envio de conteúdos e segurança.</li>
          <li><strong>Compartilhamento</strong> – Apenas com profissionais, parceiros de pagamento e autoridades.</li>
          <li><strong>Segurança</strong> – Seus dados são protegidos por criptografia.</li>
          <li><strong>Seus Direitos</strong> – Você pode solicitar correção, exclusão ou portabilidade.</li>
          <li><strong>Cookies</strong> – Usamos cookies para melhorar a navegação.</li>
          <li><strong>Alterações</strong> – A política pode ser atualizada. Notificaremos mudanças relevantes.</li>
          <li><strong>Contato</strong> – privacidade@bodyhealthy.com.br</li>
        </ol>`
    };

    function abrirModal(tipo) {
      document.getElementById('modal-texto').innerHTML = textos[tipo];
      document.getElementById('modal').style.display = 'block';
    }

    function fecharModal() {
      document.getElementById('modal').style.display = 'none';
    }