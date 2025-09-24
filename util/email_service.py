# util/email_service.py - NOVO ARQUIVO
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    def __init__(self):
        # Usar variáveis de ambiente para segurança
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = os.getenv("BODY_HEALTH_EMAIL", "suporte.bodyhealth@gmail.com")
        self.password = os.getenv("BODY_HEALTH_PASSWORD", "sua_senha_app")
    
    def enviar_mensagem_suporte(self, nome: str, email_usuario: str, 
                               assunto: str, mensagem: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.email  # Envia para próprio suporte
            msg['Subject'] = f"[BODY HEALTH SUPORTE] {assunto}"
            
            corpo = f"""
Nova mensagem de suporte:

Nome: {nome}
Email: {email_usuario}
Assunto: {assunto}

Mensagem:
{mensagem}

---
Sistema Body Health
"""
            msg.attach(MIMEText(corpo, 'plain'))
            
            # Enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            # Enviar confirmação para usuário
            self._enviar_confirmacao(email_usuario, nome)
            return True
            
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            return False
    
    def _enviar_confirmacao(self, email_usuario: str, nome: str):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = email_usuario
            msg['Subject'] = "Mensagem recebida - Body Health"
            
            corpo = f"""
Olá {nome},

Recebemos sua mensagem e nossa equipe responderá em até 24 horas.

Obrigado por entrar em contato!

Atenciosamente,
Equipe Body Health
"""
            msg.attach(MIMEText(corpo, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
                
        except Exception as e:
            print(f"Erro ao enviar confirmação: {e}")