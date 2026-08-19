"""Envío de correo vía SMTP configurado por variables de entorno.

Variables esperadas:
    SMTP_HOST      Host del servidor SMTP (si falta, el envío se simula).
    SMTP_PORT      Puerto SMTP (default 587).
    SMTP_USER      Usuario para autenticación (opcional).
    SMTP_PASSWORD  Password/app-password para autenticación (opcional).
    SMTP_FROM      Remitente (default: SMTP_USER).
    SMTP_USE_TLS   "false" para desactivar STARTTLS (default: true).
"""
import os
import smtplib
from email.message import EmailMessage


def send_email(recipient: str, subject: str, body: str) -> tuple[str, str | None]:
    """Envía un correo y devuelve (status, error_message).

    status es "sent", "simulated" (sin SMTP_HOST configurado) o "failed".
    """
    host = os.environ.get("SMTP_HOST")
    if not host:
        return "simulated", None

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM", user or "")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() != "false"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
        return "sent", None
    except Exception as exc:  # noqa: BLE001 - se registra el detalle en la BD
        return "failed", str(exc)
