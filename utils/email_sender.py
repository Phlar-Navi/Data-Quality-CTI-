"""
Module d'envoi d'emails pour le monitoring CTI.

Gère l'envoi de notifications par email avec templates HTML :
- Alertes critiques (score < 5)
- Alertes warnings (5 ≤ score < 8)
- Rapports quotidiens
- Résumés détaillés par breakpoint

Usage:
    from utils.email_sender import EmailSender
    
    sender = EmailSender(config)
    sender.send_alert(breakpoint_result, email_type="alert_critical")
    sender.send_daily_report(results_list)
"""

import smtplib
import logging
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from jinja2 import Template


class EmailSender:
    """Gestionnaire d'envoi d'emails pour le monitoring."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'email sender.
        
        Args:
            config: Configuration globale (section 'notifications.email')
        """
        self.config = config.get("notifications", {}).get("email", {})
        self.logger = logging.getLogger(__name__)
        
        # Configuration SMTP
        self.smtp_server = self.config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.use_tls = self.config.get("use_tls", True)
        self.use_ssl = self.config.get("use_ssl", False)
        
        # Authentification
        self.sender = os.getenv("EMAIL_SENDER") or self.config.get("sender")
        self.sender_password = os.getenv("EMAIL_SENDER_PASSWORD") or self.config.get("sender_password")
        self.sender_name = self.config.get("sender_name", "Monitoring CTI")
        
        # Throttling
        self.last_alert_times = {}  # {breakpoint_id: timestamp}
        self.emails_sent_timestamps = []  # Liste des timestamps d'envoi
        
        if not self.sender or not self.sender_password:
            self.logger.warning("[EMAIL] Credentials manquantes - vérifier EMAIL_SENDER et EMAIL_SENDER_PASSWORD")
    
    def _check_throttling(self, breakpoint_id: str = None) -> bool:
        """
        Vérifie si l'envoi respecte les limites de throttling.
        
        Args:
            breakpoint_id: ID du breakpoint (pour min_interval_between_alerts)
        
        Returns:
            True si l'envoi est autorisé, False sinon
        """
        current_time = time.time()
        
        # Vérifier min_interval_between_alerts
        if breakpoint_id:
            min_interval = self.config.get("min_interval_between_alerts", 300)
            last_alert = self.last_alert_times.get(breakpoint_id)
            
            if last_alert and (current_time - last_alert) < min_interval:
                self.logger.info(f"[EMAIL] Throttled : alerte pour {breakpoint_id} déjà envoyée il y a moins de {min_interval}s")
                return False
        
        # Vérifier max_emails_per_hour
        max_per_hour = self.config.get("max_emails_per_hour", 10)
        one_hour_ago = current_time - 3600
        
        # Nettoyer les timestamps > 1h
        self.emails_sent_timestamps = [ts for ts in self.emails_sent_timestamps if ts > one_hour_ago]
        
        if len(self.emails_sent_timestamps) >= max_per_hour:
            self.logger.warning(f"[EMAIL] Throttled : limite de {max_per_hour} emails/heure atteinte")
            return False
        
        return True
    
    def _record_send(self, breakpoint_id: str = None):
        """Enregistre un envoi d'email pour le throttling."""
        current_time = time.time()
        self.emails_sent_timestamps.append(current_time)
        
        if breakpoint_id:
            self.last_alert_times[breakpoint_id] = current_time
    
    def _get_recipients(self, email_type: str) -> List[str]:
        """
        Retourne les destinataires selon le type d'email.
        
        Args:
            email_type: Type d'email ('alert_critical', 'alert_warning', 'daily_report', etc.)
        
        Returns:
            Liste d'adresses email
        """
        recipients_config = self.config.get("recipients", {})
        
        # Récupérer les destinataires "all" (toujours inclus)
        all_recipients = recipients_config.get("all", [])
        
        # Ajouter les destinataires spécifiques selon le type
        if email_type in ["alert_critical", "alert_warning"]:
            specific = recipients_config.get("alerts", [])
        elif email_type in ["daily_report", "weekly_summary", "breakpoint_detail"]:
            specific = recipients_config.get("reports", [])
        else:
            specific = []
        
        # Dédupliquer et retourner
        return list(set(all_recipients + specific))
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Rend un template HTML avec le contexte fourni.
        
        Args:
            template_name: Nom du template ('alert_critical', 'daily_report', etc.)
            context: Variables à injecter dans le template
        
        Returns:
            HTML rendu
        """
        templates = {
            "alert_critical": ALERT_CRITICAL_TEMPLATE,
            "alert_warning": ALERT_WARNING_TEMPLATE,
            "daily_report": DAILY_REPORT_TEMPLATE,
            "breakpoint_detail": BREAKPOINT_DETAIL_TEMPLATE
        }
        
        template_str = templates.get(template_name, ALERT_CRITICAL_TEMPLATE)
        template = Template(template_str)
        
        return template.render(**context)
    
    def send_email(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Envoie un email générique.
        
        Args:
            to: Liste d'adresses destinataires
            subject: Sujet de l'email
            html_body: Corps HTML
            text_body: Corps texte brut (fallback)
            attachments: Liste de chemins de fichiers à joindre
        
        Returns:
            True si envoi réussi, False sinon
        """
        if not to:
            self.logger.warning("[EMAIL] Aucun destinataire configuré")
            return False
        
        if not self.sender or not self.sender_password:
            self.logger.error("[EMAIL] Credentials SMTP manquantes")
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender}>"
            msg['To'] = ", ".join(to)
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Ajouter le corps texte (fallback)
            if text_body:
                part_text = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(part_text)
            
            # Ajouter le corps HTML
            part_html = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part_html)
            
            # Ajouter les pièces jointes
            if attachments:
                for file_path in attachments:
                    if Path(file_path).exists():
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={Path(file_path).name}'
                            )
                            msg.attach(part)
            
            # Connexion SMTP et envoi
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            
            server.login(self.sender, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"[EMAIL] Email envoyé avec succès à {len(to)} destinataire(s)")
            return True
            
        except smtplib.SMTPAuthenticationError:
            self.logger.error("[EMAIL] Erreur authentification SMTP - Vérifier credentials")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"[EMAIL] Erreur SMTP : {e}")
            return False
        except Exception as e:
            self.logger.error(f"[EMAIL] Erreur inattendue : {e}", exc_info=True)
            return False
    
    def send_alert(
        self,
        breakpoint_result: Dict[str, Any],
        email_type: str = "alert_critical"
    ) -> bool:
        """
        Envoie une alerte (critique ou warning).
        
        Args:
            breakpoint_result: Dict avec résultat du breakpoint
            email_type: 'alert_critical' ou 'alert_warning'
        
        Returns:
            True si envoi réussi
        """
        breakpoint_id = breakpoint_result.get("breakpoint_id")
        
        # Vérifier throttling
        if not self._check_throttling(breakpoint_id):
            return False
        
        # Préparer le contexte
        failed_checks = [
            c for c in breakpoint_result.get("checks", [])
            if c.get("status") in ["failure", "error"]
        ]
        
        warned_checks = [
            c for c in breakpoint_result.get("checks", [])
            if c.get("status") == "warning"
        ]
        
        context = {
            "breakpoint_id": breakpoint_id,
            "breakpoint_name": breakpoint_result.get("breakpoint_name"),
            "score": breakpoint_result.get("score"),
            "target_date": breakpoint_result.get("target_date"),
            "run_timestamp": breakpoint_result.get("run_timestamp"),
            "status": breakpoint_result.get("status"),
            "failed_checks": failed_checks,
            "warned_checks": warned_checks,
            "total_checks": len(breakpoint_result.get("checks", [])),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Sujet selon le type
        if email_type == "alert_critical":
            subject = f"🚨 [URGENT] Monitoring CTI - {context['breakpoint_name']} en échec"
        else:
            subject = f"⚠️ [WARNING] Monitoring CTI - {context['breakpoint_name']} dégradé"
        
        # Rendre le template
        html_body = self._render_template(email_type, context)
        
        # Destinataires
        recipients = self._get_recipients(email_type)
        
        # Envoyer
        success = self.send_email(recipients, subject, html_body)
        
        if success:
            self._record_send(breakpoint_id)
        
        return success
    
    def send_daily_report(
        self,
        breakpoints_results: List[Dict[str, Any]],
        date: Optional[str] = None
    ) -> bool:
        """
        Envoie le rapport quotidien avec tous les breakpoints.
        
        Args:
            breakpoints_results: Liste des résultats de tous les breakpoints
            date: Date du rapport (défaut: aujourd'hui)
        
        Returns:
            True si envoi réussi
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Calculer les statistiques
        total_bp = len(breakpoints_results)
        scores = [bp.get("score", 0) for bp in breakpoints_results if bp.get("score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        critical_count = sum(1 for bp in breakpoints_results if bp.get("score", 10) < 5)
        warning_count = sum(1 for bp in breakpoints_results if 5 <= bp.get("score", 10) < 8)
        ok_count = sum(1 for bp in breakpoints_results if bp.get("score", 10) >= 8)
        
        # Préparer le contexte
        context = {
            "date": date,
            "total_breakpoints": total_bp,
            "average_score": round(avg_score, 1),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "ok_count": ok_count,
            "breakpoints": breakpoints_results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Sujet
        status_emoji = "🚨" if critical_count > 0 else ("⚠️" if warning_count > 0 else "✅")
        subject = f"{status_emoji} [RAPPORT] Monitoring CTI - Rapport quotidien {date}"
        
        # Rendre le template
        html_body = self._render_template("daily_report", context)
        
        # Destinataires
        recipients = self._get_recipients("daily_report")
        
        # Envoyer
        return self.send_email(recipients, subject, html_body)
    
    def send_breakpoint_detail(
        self,
        breakpoint_result: Dict[str, Any]
    ) -> bool:
        """
        Envoie un rapport détaillé pour un breakpoint spécifique.
        
        Args:
            breakpoint_result: Résultat du breakpoint
        
        Returns:
            True si envoi réussi
        """
        context = {
            "breakpoint_id": breakpoint_result.get("breakpoint_id"),
            "breakpoint_name": breakpoint_result.get("breakpoint_name"),
            "score": breakpoint_result.get("score"),
            "target_date": breakpoint_result.get("target_date"),
            "checks": breakpoint_result.get("checks", []),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        subject = f"📊 [DÉTAIL] Monitoring CTI - {context['breakpoint_name']}"
        
        html_body = self._render_template("breakpoint_detail", context)
        recipients = self._get_recipients("breakpoint_detail")
        
        return self.send_email(recipients, subject, html_body)
    
    def test_connection(self) -> bool:
        """
        Teste la connexion SMTP.
        
        Returns:
            True si connexion réussie
        """
        if not self.sender or not self.sender_password:
            self.logger.error("[EMAIL] Credentials manquantes pour le test")
            return False
        
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                if self.use_tls:
                    server.starttls()
            
            server.login(self.sender, self.sender_password)
            server.quit()
            
            self.logger.info("[EMAIL] Test connexion SMTP réussi ✅")
            return True
            
        except Exception as e:
            self.logger.error(f"[EMAIL] Test connexion SMTP échoué : {e}")
            return False


# ============================================================================
# TEMPLATES HTML
# ============================================================================

ALERT_CRITICAL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #f44336, #d32f2f); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 28px; }
        .alert-box { background-color: #ffebee; border-left: 6px solid #f44336; padding: 20px; margin: 20px 0; }
        .alert-box h2 { margin-top: 0; color: #c62828; }
        .metric { display: inline-block; margin-right: 30px; }
        .metric-label { font-weight: bold; color: #666; }
        .metric-value { font-size: 24px; color: #f44336; font-weight: bold; }
        .checks-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .checks-table th { background-color: #f5f5f5; padding: 12px; text-align: left; border-bottom: 2px solid #ddd; }
        .checks-table td { padding: 10px; border-bottom: 1px solid #eee; }
        .status-fail { color: #f44336; font-weight: bold; }
        .actions { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
        .actions h3 { margin-top: 0; color: #856404; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 Alerte Critique - Monitoring CTI</h1>
        <p style="margin: 10px 0 0 0;">Un problème critique a été détecté</p>
    </div>
    
    <div class="alert-box">
        <h2>Breakpoint en échec : {{ breakpoint_name }}</h2>
        <div class="metric">
            <div class="metric-label">Score</div>
            <div class="metric-value">{{ score }}/10</div>
        </div>
        <div class="metric">
            <div class="metric-label">Date analysée</div>
            <div class="metric-value" style="font-size: 18px;">{{ target_date }}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Statut</div>
            <div class="metric-value" style="font-size: 18px;">{{ status }}</div>
        </div>
    </div>
    
    {% if failed_checks %}
    <h3>❌ Checks échoués ({{ failed_checks|length }}/{{ total_checks }})</h3>
    <table class="checks-table">
        <thead>
            <tr>
                <th>Check</th>
                <th>Statut</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
            {% for check in failed_checks %}
            <tr>
                <td><strong>{{ check.name }}</strong></td>
                <td class="status-fail">❌ {{ check.status }}</td>
                <td>{{ check.message }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    
    <div class="actions">
        <h3>⚡ Actions recommandées</h3>
        <ol>
            <li><strong>Vérifier la source de données</strong> : Connexion, disponibilité, credentials</li>
            <li><strong>Analyser les logs détaillés</strong> : <code>./logs/monitoring_{{ timestamp[:10].replace('-', '') }}.log</code></li>
            <li><strong>Consulter le dashboard</strong> : <code>./dashboard_data/latest.json</code></li>
            <li><strong>Contacter l'équipe technique</strong> si le problème persiste</li>
        </ol>
    </div>
    
    <div class="footer">
        <p><strong>Monitoring CTI automatique</strong></p>
        <p>Généré le {{ timestamp }} | Breakpoint ID: {{ breakpoint_id }}</p>
        <p style="color: #ccc;">Ce message a été généré automatiquement. Ne pas répondre directement à cet email.</p>
    </div>
</body>
</html>
"""

ALERT_WARNING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #ff9800, #f57c00); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 28px; }
        .warning-box { background-color: #fff3e0; border-left: 6px solid #ff9800; padding: 20px; margin: 20px 0; }
        .warning-box h2 { margin-top: 0; color: #e65100; }
        .metric { display: inline-block; margin-right: 30px; }
        .metric-label { font-weight: bold; color: #666; }
        .metric-value { font-size: 24px; color: #ff9800; font-weight: bold; }
        .checks-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .checks-table th { background-color: #f5f5f5; padding: 12px; text-align: left; }
        .checks-table td { padding: 10px; border-bottom: 1px solid #eee; }
        .status-warn { color: #ff9800; font-weight: bold; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 40px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚠️ Alerte Warning - Monitoring CTI</h1>
        <p style="margin: 10px 0 0 0;">Service dégradé détecté</p>
    </div>
    
    <div class="warning-box">
        <h2>Breakpoint dégradé : {{ breakpoint_name }}</h2>
        <div class="metric">
            <div class="metric-label">Score</div>
            <div class="metric-value">{{ score }}/10</div>
        </div>
        <div class="metric">
            <div class="metric-label">Date</div>
            <div class="metric-value" style="font-size: 18px;">{{ target_date }}</div>
        </div>
    </div>
    
    {% if warned_checks %}
    <h3>⚠️ Checks en warning ({{ warned_checks|length }}/{{ total_checks }})</h3>
    <table class="checks-table">
        <thead>
            <tr>
                <th>Check</th>
                <th>Statut</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
            {% for check in warned_checks %}
            <tr>
                <td><strong>{{ check.name }}</strong></td>
                <td class="status-warn">⚠️ {{ check.status }}</td>
                <td>{{ check.message }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    
    {% if failed_checks %}
    <h3>❌ Checks échoués ({{ failed_checks|length }})</h3>
    <table class="checks-table">
        <tbody>
            {% for check in failed_checks %}
            <tr>
                <td><strong>{{ check.name }}</strong></td>
                <td style="color: #f44336;">❌ {{ check.status }}</td>
                <td>{{ check.message }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    
    <div class="footer">
        <p><strong>Monitoring CTI</strong> | {{ timestamp }}</p>
        <p style="color: #ccc;">Message automatique - Ne pas répondre</p>
    </div>
</body>
</html>
"""

DAILY_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
        .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #2196F3, #1976D2); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 32px; }
        .stats { display: flex; justify-content: space-around; margin: 30px 0; }
        .stat-box { text-align: center; padding: 20px; background: #f9f9f9; border-radius: 8px; flex: 1; margin: 0 10px; }
        .stat-value { font-size: 36px; font-weight: bold; margin: 10px 0; }
        .stat-label { color: #666; font-size: 14px; }
        .stat-ok { color: #4caf50; }
        .stat-warning { color: #ff9800; }
        .stat-critical { color: #f44336; }
        .bp-list { margin: 20px 0; }
        .bp-item { background: #fafafa; padding: 20px; margin: 15px 0; border-left: 4px solid #ddd; border-radius: 4px; }
        .bp-item.ok { border-left-color: #4caf50; }
        .bp-item.warning { border-left-color: #ff9800; }
        .bp-item.critical { border-left-color: #f44336; }
        .bp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .bp-name { font-weight: bold; font-size: 18px; }
        .bp-score { font-size: 28px; font-weight: bold; }
        .bp-meta { color: #666; font-size: 13px; margin-bottom: 15px; }
        .checks-summary { margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd; }
        .checks-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; margin-top: 10px; }
        .check-item { padding: 8px 12px; background: #fff; border-radius: 4px; font-size: 13px; display: flex; align-items: center; border-left: 3px solid #ddd; }
        .check-item.success { border-left-color: #4caf50; background: #f1f8f4; }
        .check-item.warning { border-left-color: #ff9800; background: #fff8e1; }
        .check-item.failure { border-left-color: #f44336; background: #ffebee; }
        .check-icon { margin-right: 8px; font-weight: bold; }
        .check-name { flex: 1; font-weight: 500; }
        .footer { text-align: center; color: #999; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }
        .summary-text { background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #2196F3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Rapport Quotidien - Monitoring CTI</h1>
            <p style="margin: 10px 0 0 0; font-size: 18px;">{{ date }}</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Breakpoints</div>
                <div class="stat-value">{{ total_breakpoints }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Score moyen</div>
                <div class="stat-value" style="color: #2196F3;">{{ average_score }}/10</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">✅ OK</div>
                <div class="stat-value stat-ok">{{ ok_count }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">⚠️ Warnings</div>
                <div class="stat-value stat-warning">{{ warning_count }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">🚨 Critiques</div>
                <div class="stat-value stat-critical">{{ critical_count }}</div>
            </div>
        </div>
        
        {% if warning_count > 0 or critical_count > 0 %}
        <div class="summary-text">
            <strong>⚠️ Points d'attention :</strong>
            {% if critical_count > 0 %}
            <span style="color: #f44336;">{{ critical_count }} breakpoint(s) critique(s) détecté(s).</span>
            {% endif %}
            {% if warning_count > 0 %}
            <span style="color: #ff9800;">{{ warning_count }} breakpoint(s) dégradé(s).</span>
            {% endif %}
            Veuillez consulter les détails ci-dessous.
        </div>
        {% else %}
        <div class="summary-text" style="background: #e8f5e9; border-left-color: #4caf50;">
            <strong>✅ Tous les systèmes sont opérationnels</strong> - Aucune anomalie détectée.
        </div>
        {% endif %}
        
        <h2>Détail des breakpoints</h2>
        <div class="bp-list">
            {% for bp in breakpoints %}
            <div class="bp-item {% if bp.score >= 8 %}ok{% elif bp.score >= 5 %}warning{% else %}critical{% endif %}">
                <div class="bp-header">
                    <div class="bp-name">
                        {% if bp.score >= 8 %}✅{% elif bp.score >= 5 %}⚠️{% else %}🚨{% endif %}
                        {{ bp.breakpoint_name }}
                    </div>
                    <div class="bp-score {% if bp.score >= 8 %}stat-ok{% elif bp.score >= 5 %}stat-warning{% else %}stat-critical{% endif %}">
                        {{ bp.score }}/10
                    </div>
                </div>
                <div class="bp-meta">
                    ID: {{ bp.breakpoint_id }} | Date: {{ bp.target_date }} | Checks: {{ bp.checks|length }}
                </div>
                
                <div class="checks-summary">
                    <strong>Résumé des checks :</strong>
                    <div style="margin: 5px 0; font-size: 13px; color: #666;">
                        {% set success_count = bp.checks | selectattr("status", "equalto", "success") | list | length %}
                        {% set warning_count = bp.checks | selectattr("status", "equalto", "warning") | list | length %}
                        {% set failure_count = bp.checks | selectattr("status", "in", ["failure", "error"]) | list | length %}
                        <span style="color: #4caf50;">✓ {{ success_count }} réussi(s)</span>
                        {% if warning_count > 0 %}
                        | <span style="color: #ff9800;">⚠ {{ warning_count }} warning(s)</span>
                        {% endif %}
                        {% if failure_count > 0 %}
                        | <span style="color: #f44336;">✗ {{ failure_count }} échoué(s)</span>
                        {% endif %}
                    </div>
                    
                    <div class="checks-grid">
                        {% for check in bp.checks %}
                        <div class="check-item {{ check.status }}">
                            <span class="check-icon">
                                {% if check.status == 'success' %}✓{% elif check.status == 'warning' %}⚠{% else %}✗{% endif %}
                            </span>
                            <span class="check-name">{{ check.name.replace('_check', '').replace('_', ' ').title() }}</span>
                        </div>
                        {% endfor %}
                    </div>
                    
                    {% if failure_count > 0 or warning_count > 0 %}
                    <div style="margin-top: 15px; padding: 10px; background: #fff; border-radius: 4px; font-size: 13px;">
                        <strong>Détails des problèmes :</strong>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            {% for check in bp.checks %}
                            {% if check.status in ['failure', 'warning', 'error'] %}
                            <li style="margin: 5px 0;">
                                <strong>{{ check.name.replace('_check', '').replace('_', ' ').title() }}</strong> :
                                {{ check.message }}
                            </li>
                            {% endif %}
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p><strong>Monitoring CTI</strong></p>
            <p>Rapport généré le {{ timestamp }}</p>
            <p style="color: #ccc; font-size: 11px;">Message automatique - Ne pas répondre</p>
        </div>
    </div>
</body>
</html>
"""

BREAKPOINT_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #673AB7, #512DA8); color: white; padding: 30px; border-radius: 8px; }
        .header h1 { margin: 0; }
        .summary { background: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .checks-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .checks-table th { background-color: #673AB7; color: white; padding: 12px; text-align: left; }
        .checks-table td { padding: 10px; border-bottom: 1px solid #eee; }
        .status-success { color: #4caf50; }
        .status-warning { color: #ff9800; }
        .status-failure { color: #f44336; }
        .footer { text-align: center; color: #999; margin-top: 40px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Détail Breakpoint - {{ breakpoint_name }}</h1>
        <p>{{ breakpoint_id }} | {{ target_date }}</p>
    </div>
    
    <div class="summary">
        <h2>Résumé</h2>
        <p><strong>Score :</strong> {{ score }}/10</p>
        <p><strong>Nombre de checks :</strong> {{ checks|length }}</p>
    </div>
    
    <h2>Détail des checks</h2>
    <table class="checks-table">
        <thead>
            <tr>
                <th>Check</th>
                <th>Statut</th>
                <th>Confiance</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
            {% for check in checks %}
            <tr>
                <td><strong>{{ check.name }}</strong></td>
                <td class="status-{{ check.status }}">
                    {% if check.status == 'success' %}✅{% elif check.status == 'warning' %}⚠️{% else %}❌{% endif %}
                    {{ check.status }}
                </td>
                <td>{{ check.confidence }}</td>
                <td>{{ check.message }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="footer">
        <p><strong>Monitoring CTI</strong> | {{ timestamp }}</p>
        <p style="color: #ccc;">Message automatique</p>
    </div>
</body>
</html>
"""


# CLI pour tests
if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path
    
    # Charger les variables d'environnement depuis .env
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"[ENV] Variables chargées depuis {env_path}")
        else:
            print(f"[WARN] Fichier .env introuvable : {env_path}")
    except ImportError:
        print("[WARN] python-dotenv non installé")
    
    parser = argparse.ArgumentParser(description="Email Sender - Tests")
    parser.add_argument("--test-config", action="store_true", help="Tester la configuration SMTP")
    parser.add_argument("--test-send", action="store_true", help="Envoyer un email de test")
    parser.add_argument("--to", type=str, help="Destinataire pour test")
    
    args = parser.parse_args()
    
    # Configuration de test
    test_config = {
        "notifications": {
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True,
                "recipients": {
                    "all": [args.to] if args.to else []
                }
            }
        }
    }
    
    sender = EmailSender(test_config)
    
    if args.test_config:
        print("🧪 Test de configuration SMTP...")
        if sender.test_connection():
            print("✅ Configuration OK")
            sys.exit(0)
        else:
            print("❌ Configuration KO")
            sys.exit(1)
    
    elif args.test_send:
        if not args.to:
            print("❌ --to requis pour test d'envoi")
            sys.exit(1)
        
        print(f"📧 Envoi d'un email de test à {args.to}...")
        
        # Email de test simple
        mock_result = {
            "breakpoint_id": "test_bp",
            "breakpoint_name": "Test Breakpoint",
            "score": 3,
            "target_date": "2026-09-12",
            "run_timestamp": datetime.now().isoformat(),
            "status": "Critique",
            "checks": [
                {"name": "test_check_1", "status": "failure", "message": "Test échec"},
                {"name": "test_check_2", "status": "success", "message": "Test OK"}
            ]
        }
        
        if sender.send_alert(mock_result, "alert_critical"):
            print("✅ Email de test envoyé")
            sys.exit(0)
        else:
            print("❌ Échec envoi email")
            sys.exit(1)
    
    else:
        parser.print_help()
