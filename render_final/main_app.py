from flask import Flask, request, Response, session
import random
from werkzeug.test import create_environ
from werkzeug.wrappers import Request
import uuid
from app import create_app as create_prototyp_app
from app_neutral import create_app as create_prototyp_neutral_app

app = Flask(__name__, static_folder='static', static_url_path='/static')


app1 = create_prototyp_app()
app2 = create_prototyp_neutral_app()


# Dictionary zur Speicherung der Nutzer-zu-App-Zuordnung
user_app_mapping = {}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    # Überprüfen, ob der Nutzer bereits eine ID hat
    user_id = request.cookies.get('user_id')
    user_app = request.cookies.get('user_app')
    new_user = False  # Flag, um später zu erkennen, ob wir Cookies setzen müssen

    # Wenn keine user_id vorhanden → neu generieren
    if not user_id:
        user_id = str(uuid.uuid4())
        new_user = True
        print(f"Neue user_id generiert: {user_id}")

    # Wenn keine app-Zuordnung vorhanden → einmalig zufällig zuweisen
    if not user_app:
        user_app = random.choice(['app1', 'app2'])
        new_user = True
        print(f"App {user_app} für {user_id} zugewiesen")

    # zugewiesene App laden
    selected_app = app1 if user_app == 'app1' else app2
    print(f"Selected App: {selected_app}")
    print(f"Request Path: {path}")


    if path.startswith('static/'):
        print(f"Handling static file: {path}")
        with selected_app.test_request_context(path=path, method=request.method, headers=dict(request.headers)):
            response = selected_app.full_dispatch_request()
        return Response(
            response=response.get_data(),
            status=response.status_code,
            headers=dict(response.headers),
        )


    headers = dict(request.headers)

    # neue Umgebung für die ausgewählte App
    environ = create_environ(
        path=request.path,
        method=request.method,
        headers=headers,  # veränderliches Dictionary verwenden
        data=request.get_data(),
        query_string=request.query_string,
        content_type=request.content_type,
    )

    # Request-Objekt für die ausgewählte App erstellen
    with selected_app.request_context(environ):
        # Anfrage mit der ausgewählten App verarbeiten
        response = selected_app.full_dispatch_request()

    # Response erstellen und Cookie setzen
    flask_response = Response(
        response=response.get_data(),
        status=response.status_code,
        headers=dict(response.headers),
    )
    if new_user:
        flask_response.set_cookie('user_id', user_id, max_age=60 * 60 * 24 * 365)
        flask_response.set_cookie('user_app', user_app, max_age=60 * 60 * 24 * 365)

    return flask_response
if __name__ == "__main__":
    app.run(debug=True)