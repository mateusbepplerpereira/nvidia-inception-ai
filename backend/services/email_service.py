import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional
from datetime import datetime

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "mailhog")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@nvidia-inception.com")

    def send_newsletter_report(
        self,
        recipients: List[str],
        startup_data: List[dict],
        startup_count: int = 0
    ) -> bool:
        """
        Envia relatório de startups por email para a lista de newsletter
        """
        try:
            # Criar conexão SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            # Login se necessário (MailHog não precisa)
            if self.smtp_username and self.smtp_password:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)

            # Preparar o email
            subject = f"Relatório de Startups - {datetime.now().strftime('%d/%m/%Y')}"

            # Corpo do email em HTML com fonte Arial
            html_body = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    h2, h3, h4 {{
                        font-family: Arial, sans-serif;
                        color: #2c3e50;
                    }}
                    .summary-box {{
                        background-color: #f0f0f0;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                        border-left: 4px solid #76b900;
                    }}
                    ul {{
                        padding-left: 20px;
                    }}
                    li {{
                        margin-bottom: 5px;
                    }}
                    .footer {{
                        font-size: 12px;
                        color: #666;
                        border-top: 1px solid #eee;
                        padding-top: 15px;
                        margin-top: 30px;
                    }}
                </style>
            </head>
            <body>
                <h2>Relatório de Descoberta de Startups</h2>

                <div class="summary-box">
                    <h3>Resumo do Relatório</h3>
                    <ul>
                        <li><strong>Startups encontradas:</strong> {startup_count}</li>
                        <li><strong>Setor:</strong> {startup_data[0].get('sector', 'N/A') if startup_data else 'N/A'}</li>
                        <li><strong>País/Região:</strong> {startup_data[0].get('country', 'N/A') if startup_data else 'N/A'}</li>
                        <li><strong>Data de geração:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</li>
                    </ul>
                </div>

                {self._generate_startup_table_html(startup_data)}

                <div class="footer">
                    NVIDIA Inception AI
                </div>
            </body>
            </html>
            """

            # Enviar para cada destinatário
            for recipient in recipients:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = self.from_email
                msg["To"] = recipient

                # Adicionar corpo do email
                html_part = MIMEText(html_body, "html", "utf-8")
                msg.attach(html_part)

                # Não há mais anexo - dados já estão no corpo do email

                # Enviar email
                server.send_message(msg)
                print(f"Email enviado para: {recipient}")

            server.quit()
            return True

        except Exception as e:
            print(f"❌ Erro ao enviar emails: {str(e)}")
            return False

    def _generate_startup_table_html(self, startup_data: List[dict]) -> str:
        """
        Gera tabela HTML com informações das startups
        """
        if not startup_data:
            return """
            <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 5px; margin: 20px 0;">
                <p style="color: #666; margin: 0;">Nenhuma startup encontrada para este relatório.</p>
            </div>
            """

        table_html = """
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-family: Arial, sans-serif;">
            <thead>
                <tr style="background-color: #76b900; color: white;">
                    <th style="padding: 12px 8px; text-align: left; border: 1px solid #ddd;">Nome</th>
                    <th style="padding: 12px 8px; text-align: left; border: 1px solid #ddd;">Setor</th>
                    <th style="padding: 12px 8px; text-align: left; border: 1px solid #ddd;">País</th>
                    <th style="padding: 12px 8px; text-align: left; border: 1px solid #ddd;">Tecnologias</th>
                    <th style="padding: 12px 8px; text-align: left; border: 1px solid #ddd;">Score</th>
                </tr>
            </thead>
            <tbody>
        """

        for i, startup in enumerate(startup_data):
            row_color = "#f9f9f9" if i % 2 == 0 else "#ffffff"
            table_html += f"""
                <tr style="background-color: {row_color};">
                    <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">
                        <strong style="color: #2c3e50;">{startup['name']}</strong><br>
                        <small style="color: #666;">{startup['city']}, {startup['country']}</small><br>
                        {f'<a href="{startup["website"]}" style="color: #76b900; text-decoration: none; font-size: 12px;" target="_blank">Website</a>' if startup['website'] != 'N/A' else ''}
                    </td>
                    <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">
                        <span style="background-color: #e7f3ff; color: #1565c0; padding: 2px 6px; border-radius: 3px; font-size: 11px;">
                            {startup['sector']}
                        </span><br>
                        <small style="color: #666;">Fund. {startup['founded_year']}</small>
                    </td>
                    <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">
                        {startup['country']}
                    </td>
                    <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top;">
                        <small style="color: #555;">{startup['ai_technologies']}</small>
                    </td>
                    <td style="padding: 10px 8px; border: 1px solid #ddd; vertical-align: top; text-align: center;">
                        <span style="background-color: #4caf50; color: white; padding: 4px 8px; border-radius: 12px; font-weight: bold; font-size: 12px;">
                            {startup['total_score']}
                        </span>
                    </td>
                </tr>
                <tr style="background-color: {row_color};">
                    <td colspan="5" style="padding: 8px; border: 1px solid #ddd; border-top: none;">
                        <small style="color: #555; font-style: italic;">{startup['description']}</small>
                    </td>
                </tr>
            """

        table_html += """
            </tbody>
        </table>
        """

        return table_html

