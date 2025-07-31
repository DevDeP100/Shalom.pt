"""
Backend personalizado para lidar com certificados SSL
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage


class UnsafeTLSBackend(EmailBackend):
    """
    Backend de email que desabilita a verificação de certificados SSL
    para resolver problemas com certificados auto-assinados
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None
    
    def open(self):
        """
        Abre conexão SMTP com SSL desabilitado
        """
        if self.connection:
            return False
        
        try:
            # Criar contexto SSL sem verificação de certificado
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            if self.use_ssl:
                # Conexão SSL
                self.connection = smtplib.SMTP_SSL(
                    self.host, 
                    self.port, 
                    timeout=self.timeout,
                    context=ssl_context
                )
            else:
                # Conexão normal com TLS
                self.connection = smtplib.SMTP(
                    self.host, 
                    self.port, 
                    timeout=self.timeout
                )
                if self.use_tls:
                    self.connection.starttls(context=ssl_context)
            
            # Autenticar se credenciais fornecidas
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
            
        except Exception as e:
            if not self.fail_silently:
                raise e
            return False
    
    def close(self):
        """
        Fecha a conexão SMTP
        """
        if self.connection is None:
            return
        
        try:
            self.connection.quit()
        except smtplib.SMTPServerDisconnected:
            pass
        finally:
            self.connection = None
    
    def send_messages(self, email_messages):
        """
        Envia mensagens de email
        """
        if not email_messages:
            return 0
        
        if not self.open():
            return 0
        
        num_sent = 0
        
        for message in email_messages:
            sent = self._send(message)
            if sent:
                num_sent += 1
        
        return num_sent
    
    def _send(self, email_message):
        """
        Envia uma mensagem de email
        """
        if not email_message.recipients():
            return False
        
        encoding = email_message.encoding or 'utf-8'
        from_email = email_message.from_email or self.username
        recipients = email_message.recipients()
        
        try:
            self.connection.sendmail(
                from_email,
                recipients,
                email_message.message().as_bytes()
            )
            return True
        except Exception as e:
            if not self.fail_silently:
                raise e
            return False 