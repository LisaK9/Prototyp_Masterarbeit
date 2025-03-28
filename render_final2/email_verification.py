import random
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import smtplib

verification_codes = {}

def generate_code():
    """Generiert einen eindeutigen 6-stelligen Code."""
    print("Generiere Code...")  # Debug-Ausgabe
    return ''.join(random.choices(string.digits, k=6))

def send_email(email, code):
    """Sendet den Verifizierungscode an die angegebene E-Mail-Adresse."""
    print(f"Versuche, E-Mail an {email} zu senden...")  # Debug-Ausgabe
    sender_email = "deine_email@web.de"  # Ersetze dies durch deine Web.de-E-Mail-Adresse
    sender_password = "dein_passwort"  # Ersetze dies durch dein Web.de-Passwort oder App-Passwort

    message = MIMEText(f"Dein Verifizierungscode lautet: {code}")
    message['Subject'] = 'Dein Verifizierungscode'
    message['From'] = sender_email
    message['To'] = email

    try:
        print("Versuche, eine Verbindung zum SMTP-Server herzustellen...")  # Debug-Ausgabe
        with smtplib.SMTP('smtp.web.de', 465) as server:  # Verwende Port 587 für STARTTLS
            print("Verbindung zum SMTP-Server hergestellt. Starte TLS...")  # Debug-Ausgabe
            server.starttls()  # Aktiviere STARTTLS-Verschlüsselung
            print("TLS gestartet. Versuche, mich anzumelden...")  # Debug-Ausgabe
            server.login(sender_email, sender_password)
            print("Anmeldung erfolgreich. Versende E-Mail...")  # Debug-Ausgabe
            server.sendmail(sender_email, [email], message.as_string())
            print(f"E-Mail an {email} gesendet.")  # Debug-Ausgabe
        return True
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")  # Debug-Ausgabe
        return False

def store_code(email, code):
    """Speichert den Code mit einer Gültigkeitsdauer von 10 Minuten."""
    print(f"Speichere Code für {email}...")  # Debug-Ausgabe
    expiration_time = datetime.now() + timedelta(minutes=10)
    verification_codes[email] = {'code': code, 'expires': expiration_time}

def verify_code(email, code):
    """Überprüft, ob der eingegebene Code korrekt und noch gültig ist."""
    print(f"Überprüfe Code für {email}...")  # Debug-Ausgabe
    if email in verification_codes:
        stored_code = verification_codes[email]
        if datetime.now() <= stored_code['expires'] and code == stored_code['code']:
            del verification_codes[email]  # Lösche den Code nach erfolgreicher Verifizierung
            return True
    return False