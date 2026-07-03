import os
from typing import List, Dict, Any, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, MimeType
from jinja2 import Template
from loguru import logger
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

class EmailNotifier:
    """Email notification service"""
    
    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "sendgrid")  # sendgrid or smtp
        self.from_email = os.getenv("EMAIL_FROM", "alerts@vehiclemonitoring.com")
        
        if self.provider == "sendgrid":
            self.sg_client = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        
        self.templates = self._load_templates()
        logger.info("Email notifier initialized")
    
    def _load_templates(self) -> Dict[str, Template]:
        """Load email templates"""
        templates = {
            "alert": Template("""
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .alert-critical { background-color: #ff4444; color: white; padding: 20px; }
                    .alert-high { background-color: #ff8800; color: white; padding: 20px; }
                    .alert-medium { background-color: #ffbb33; color: black; padding: 20px; }
                    .alert-low { background-color: #00C851; color: white; padding: 20px; }
                    .details { padding: 20px; background-color: #f5f5f5; }
                    .actions { padding: 20px; }
                    .button { 
                        background-color: #007bff; 
                        color: white; 
                        padding: 10px 20px; 
                        text-decoration: none; 
                        border-radius: 5px; 
                    }
                </style>
            </head>
            <body>
                <h1>Vehicle Condition Alert</h1>
                <div class="alert-{{ severity.lower() }}">
                    <h2>{{ severity }} Severity Alert</h2>
                    <p><strong>Vehicle:</strong> {{ vehicle_id }}</p>
                    <p><strong>Time:</strong> {{ timestamp }}</p>
                </div>
                
                <div class="details">
                    <h3>Alert Details</h3>
                    <p>{{ message }}</p>
                    
                    {% if diagnosis %}
                    <h4>Diagnosis:</h4>
                    <ul>
                        {% for diag in diagnosis %}
                        <li>
                            <strong>{{ diag.sensor }}:</strong> 
                            Current: {{ diag.current_value }}, 
                            Normal Range: {{ diag.normal_range }}
                            <br>
                            <em>Possible Causes:</em> {{ diag.possible_causes|join(', ') }}
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                
                <div class="actions">
                    <h3>Recommended Actions:</h3>
                    <ul>
                        {% for action in recommended_actions %}
                        <li>{{ action }}</li>
                        {% endfor %}
                    </ul>
                    
                    <a href="{{ dashboard_url }}" class="button">View Dashboard</a>
                </div>
            </body>
            </html>
            """),
            
            "summary": Template("""
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .header { background-color: #007bff; color: white; padding: 20px; }
                    .content { padding: 20px; }
                    .statistics { 
                        display: flex; 
                        justify-content: space-around; 
                        margin: 20px 0; 
                    }
                    .stat-box { 
                        padding: 20px; 
                        background-color: #f5f5f5; 
                        border-radius: 5px; 
                        text-align: center; 
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Vehicle Monitoring System - {{ summary_type }} Summary</h1>
                    <p>Period: {{ start_time }} - {{ end_time }}</p>
                </div>
                
                <div class="content">
                    <div class="statistics">
                        <div class="stat-box">
                            <h3>Total Alerts</h3>
                            <p style="font-size: 2em;">{{ total_alerts }}</p>
                        </div>
                        <div class="stat-box">
                            <h3>Critical</h3>
                            <p style="font-size: 2em; color: red;">{{ critical_alerts }}</p>
                        </div>
                        <div class="stat-box">
                            <h3>Anomalies</h3>
                            <p style="font-size: 2em;">{{ total_anomalies }}</p>
                        </div>
                    </div>
                    
                    <h2>Vehicles Requiring Attention</h2>
                    <ul>
                        {% for vehicle in vehicles_needing_attention %}
                        <li>
                            <strong>{{ vehicle.id }}</strong>: 
                            Health Score: {{ vehicle.health_score }}%
                            ({{ vehicle.open_alerts }} open alerts)
                        </li>
                        {% endfor %}
                    </ul>
                    
                    <a href="{{ dashboard_url }}" class="button">View Full Dashboard</a>
                </div>
            </body>
            </html>
            """)
        }
        return templates
    
    async def send_alert(
        self,
        to_emails: List[str],
        alert_data: Dict[str, Any],
        cc_emails: Optional[List[str]] = None
    ) -> bool:
        """Send alert email"""
        try:
            subject = f"[{alert_data.get('severity', 'INFO')}] Vehicle Alert - {alert_data.get('vehicle_id', 'Unknown')}"
            
            html_content = self.templates["alert"].render(
                severity=alert_data.get('severity', 'INFO'),
                vehicle_id=alert_data.get('vehicle_id', 'Unknown'),
                timestamp=alert_data.get('timestamp', ''),
                message=alert_data.get('message', ''),
                diagnosis=alert_data.get('diagnosis', []),
                recommended_actions=alert_data.get('recommended_actions', []),
                dashboard_url=os.getenv('DASHBOARD_URL', 'http://localhost:8501')
            )
            
            if self.provider == "sendgrid":
                await self._send_via_sendgrid(
                    to_emails, subject, html_content, cc_emails
                )
            else:
                await self._send_via_smtp(
                    to_emails, subject, html_content, cc_emails
                )
            
            logger.info(f"Alert email sent to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return False
    
    async def send_summary(
        self,
        to_emails: List[str],
        summary_data: Dict[str, Any]
    ) -> bool:
        """Send summary email"""
        try:
            subject = f"Vehicle Monitoring {summary_data.get('summary_type', 'Daily')} Summary"
            
            html_content = self.templates["summary"].render(
                summary_type=summary_data.get('summary_type', 'Daily'),
                start_time=summary_data.get('start_time', ''),
                end_time=summary_data.get('end_time', ''),
                total_alerts=summary_data.get('total_alerts', 0),
                critical_alerts=summary_data.get('critical_alerts', 0),
                total_anomalies=summary_data.get('total_anomalies', 0),
                vehicles_needing_attention=summary_data.get('vehicles_needing_attention', []),
                dashboard_url=os.getenv('DASHBOARD_URL', 'http://localhost:8501')
            )
            
            if self.provider == "sendgrid":
                await self._send_via_sendgrid(to_emails, subject, html_content)
            else:
                await self._send_via_smtp(to_emails, subject, html_content)
            
            logger.info(f"Summary email sent to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send summary email: {str(e)}")
            return False
    
    async def _send_via_sendgrid(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        cc_emails: Optional[List[str]] = None
    ):
        """Send email via SendGrid"""
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=[To(email) for email in to_emails],
            subject=subject,
            html_content=Content(MimeType.html, html_content)
        )
        
        if cc_emails:
            message.cc = [Email(email) for email in cc_emails]
        
        response = self.sg_client.send(message)
        
        if response.status_code != 202:
            raise Exception(f"SendGrid error: {response.status_code}")
    
    async def _send_via_smtp(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        cc_emails: Optional[List[str]] = None
    ):
        """Send email via SMTP"""
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        msg = MIMEMultipart()
        msg["From"] = self.from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
        
        msg.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)