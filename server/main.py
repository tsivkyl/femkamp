from pathlib import Path

from flask import Flask, send_from_directory

from database import DATABASE_PATH, db
from routes import routes


BASE_DIR = Path(__file__).resolve().parent
CLIENT_DIR = BASE_DIR.parent / "client"


def create_app():
    app = Flask(__name__)

    # Flask behöver veta vilken databasfil som ska användas.
    # Vi pekar explicit på server/database.db så SQLite-filen alltid hamnar rätt.
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"

    # Stänger av en SQLAlchemy-feature som mest skapar extra minnesanvändning
    # och varningar om man inte aktivt använder den.
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Här kopplas SQLAlchemy-objektet från database.py ihop med Flask-appen.
    db.init_app(app)

    # Skapar tabellerna i database.db om de inte redan finns.
    # Befintliga tabeller och sparade resultat raderas inte.
    with app.app_context():
        db.create_all()

    app.register_blueprint(routes)

    @app.get("/")
    def index():
        # Serverar frontend-filen så du kan öppna appen via Flask-servern.
        return send_from_directory(CLIENT_DIR, "index.html")

    return app


app = create_app()


if __name__ == "__main__":
    # debug=True är smidigt lokalt eftersom servern laddar om när kod ändras.
    app.run(debug=True)
