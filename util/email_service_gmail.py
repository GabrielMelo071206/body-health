# util/email_service.py - VERSÃO MELHORADA
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional
import logging

# Configurar logging para debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Configurações do servidor SMTP
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = "bodyhealth619@gmail.com"
        # Use o código de acesso fornecido como senha de app
        self.password = "mlsn.db4526ae6121f8b073ce1e4114eec60fdfb114fe5943921ce62290543f6a4666"
        
        # Você também pode usar variáveis de ambiente se preferir
        # self.password = os.getenv("BODY_HEALTH_APP_PASSWORD", "mlsn.db4526ae6121f8b073ce1e4114eec60fdfb114fe5943921ce62290543f6a4666")
    
    def testar_conexao(self) -> bool:
        """Testa a conexão com o servidor SMTP"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                logger.info("Conexão SMTP testada com sucesso!")
                return True
        except Exception as e:
            logger.error(f"Erro na conexão SMTP: {e}")
            return False
    
    def enviar_mensagem_suporte(self, nome: str, email_usuario: str, 
                               assunto: str, mensagem: str) -> tuple[bool, str]:
        """
        Envia mensagem de suporte e retorna status e mensagem de resultado
        
        Returns:
            tuple: (sucesso: bool, mensagem: str)
        """
        try:
            # Primeira verificação: testar conexão
            if not self.testar_conexao():
                return False, "Erro de conexão com servidor de email"
            
            # Preparar mensagem para suporte
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("Body Health Sistema", self.email))
            msg['To'] = self.email
            msg['Subject'] = f"[SUPORTE] {assunto}"
            msg['Reply-To'] = email_usuario
            
            # Corpo da mensagem em texto simples
            corpo_texto = f"""
NOVA MENSAGEM DE SUPORTE

De: {nome}
Email: {email_usuario}
Assunto: {assunto}

Mensagem:
{mensagem}

---
Sistema Body Health - Mensagem recebida automaticamente
Para responder, use o email: {email_usuario}
"""
            
            # Corpo da mensagem em HTML
            corpo_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #007bff; color: white; padding: 15px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .info {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }}
        .footer {{ text-align: center; padding: 10px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Nova Mensagem de Suporte</h2>
        </div>
        <div class="content">
            <div class="info">
                <strong>Nome:</strong> {nome}<br>
                <strong>Email:</strong> <a href="mailto:{email_usuario}">{email_usuario}</a><br>
                <strong>Assunto:</strong> {assunto}
            </div>
            <div class="info">
                <strong>Mensagem:</strong><br>
                {mensagem.replace(chr(10), '<br>')}
            </div>
        </div>
        <div class="footer">
            Sistema Body Health - Mensagem recebida automaticamente<br>
            Para responder, clique no email do remetente
        </div>
    </div>
</body>
</html>
"""
            
            # Anexar ambas as versões
            part_texto = MIMEText(corpo_texto, 'plain', 'utf-8')
            part_html = MIMEText(corpo_html, 'html', 'utf-8')
            msg.attach(part_texto)
            msg.attach(part_html)
            
            # Enviar mensagem para suporte
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Email de suporte enviado de {email_usuario}")
            
            # Enviar confirmação para o usuário
            confirmacao_enviada = self._enviar_confirmacao(email_usuario, nome, assunto)
            
            if confirmacao_enviada:
                return True, "Mensagem enviada com sucesso! Você receberá uma confirmação no seu email."
            else:
                return True, "Mensagem enviada com sucesso!"
            
        except smtplib.SMTPAuthenticationError:
            logger.error("Erro de autenticação SMTP")
            return False, "Erro de autenticação do servidor de email"
        except smtplib.SMTPException as e:
            logger.error(f"Erro SMTP: {e}")
            return False, f"Erro no servidor de email: {str(e)}"
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar email: {e}")
            return False, "Erro interno do sistema. Tente novamente."
    
    def _enviar_confirmacao(self, email_usuario: str, nome: str, assunto_original: str) -> bool:
        """Envia email de confirmação para o usuário"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("Body Health Suporte", self.email))
            msg['To'] = email_usuario
            msg['Subject'] = "Confirmação - Sua mensagem foi recebida"
            
            # Corpo em texto simples
            corpo_texto = f"""
Olá {nome},

Confirmamos que recebemos sua mensagem com o assunto: "{assunto_original}"

Nossa equipe de suporte analisará sua solicitação e responderá em até 24 horas úteis.

Se sua solicitação for urgente, você também pode entrar em contato via WhatsApp:
(28) 99256-6961

Obrigado por escolher o Body Health!

Atenciosamente,
Equipe Body Health
bodyhealth619@gmail.com
"""
            
            # Corpo em HTML
            corpo_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f8f9fa; }}
        .highlight {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #28a745; }}
        .contact {{ background: #007bff; color: white; padding: 15px; text-align: center; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ Mensagem Recebida!</h2>
        </div>
        <div class="content">
            <p>Olá <strong>{nome}</strong>,</p>
            
            <div class="highlight">
                Confirmamos que recebemos sua mensagem:<br>
                <strong>Assunto:</strong> {assunto_original}
            </div>
            
            <p>Nossa equipe de suporte analisará sua solicitação e responderá em até <strong>24 horas úteis</strong>.</p>
            
            <div class="contact">
                <strong>Contato Urgente via WhatsApp:</strong><br>
                📱 (28) 99256-6961
            </div>
            
            <p>Obrigado por escolher o Body Health!</p>
        </div>
        <div class="footer">
            <strong>Equipe Body Health</strong><br>
            📧 bodyhealth619@gmail.com<br>
            <small>Esta é uma mensagem automática, não responda este email.</small>
        </div>
    </div>
</body>
</html>
"""
            
            # Anexar versões
            part_texto = MIMEText(corpo_texto, 'plain', 'utf-8')
            part_html = MIMEText(corpo_html, 'html', 'utf-8')
            msg.attach(part_texto)
            msg.attach(part_html)
            
            # Enviar confirmação
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Confirmação enviada para {email_usuario}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar confirmação: {e}")
            return False
    
    def enviar_recuperacao_senha(self, email_usuario: str, nome: str, nova_senha: str) -> tuple[bool, str]:
        """Envia email de recuperação de senha"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("Body Health Sistema", self.email))
            msg['To'] = email_usuario
            msg['Subject'] = "Body Health - Nova Senha"
            
            corpo_texto = f"""
Olá {nome},

Sua nova senha temporária foi gerada com sucesso:

NOVA SENHA: {nova_senha}

Por segurança:
1. Faça login com esta senha
2. Altere para uma senha de sua preferência
3. Não compartilhe esta informação

Se você não solicitou esta alteração, entre em contato conosco imediatamente.

Atenciosamente,
Equipe Body Health
"""
            
            corpo_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background: #f8f9fa; }}
        .password-box {{ background: #fff3cd; border: 2px solid #ffc107; padding: 20px; text-align: center; margin: 20px 0; }}
        .warning {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0; }}
        .steps {{ background: white; padding: 20px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔐 Nova Senha Gerada</h2>
        </div>
        <div class="content">
            <p>Olá <strong>{nome}</strong>,</p>
            
            <p>Sua nova senha temporária foi gerada com sucesso:</p>
            
            <div class="password-box">
                <h3>NOVA SENHA</h3>
                <code style="font-size: 18px; font-weight: bold;">{nova_senha}</code>
            </div>
            
            <div class="steps">
                <h4>Por segurança, siga estes passos:</h4>
                <ol>
                    <li>Faça login com esta senha</li>
                    <li>Altere para uma senha de sua preferência</li>
                    <li>Não compartilhe esta informação</li>
                </ol>
            </div>
            
            <div class="warning">
                <strong>⚠️ Importante:</strong> Se você não solicitou esta alteração, 
                entre em contato conosco imediatamente!
            </div>
        </div>
        <div class="footer">
            <strong>Equipe Body Health</strong><br>
            📧 bodyhealth619@gmail.com
        </div>
    </div>
</body>
</html>
"""
            
            part_texto = MIMEText(corpo_texto, 'plain', 'utf-8')
            part_html = MIMEText(corpo_html, 'html', 'utf-8')
            msg.attach(part_texto)
            msg.attach(part_html)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True, "Email de recuperação enviado com sucesso!"
            
        except Exception as e:
            logger.error(f"Erro ao enviar recuperação: {e}")
            return False, "Erro ao enviar email de recuperação"


# Instância global do serviço
email_service_gmail = EmailService()


# Função de conveniência para uso direto
def enviar_email_suporte(nome: str, email: str, assunto: str, mensagem: str) -> tuple[bool, str]:
    """Função de conveniência para enviar email de suporte"""
    return email_service_gmail.enviar_mensagem_suporte(nome, email, assunto, mensagem)


def testar_email_service():
    """Função para testar o serviço de email"""
    service = EmailService()
    if service.testar_conexao():
        print("✅ Serviço de email configurado corretamente!")
    else:
        print("❌ Erro na configuração do email")


if __name__ == "__main__":
    # Teste rápido
    testar_email_service()