from pathlib import Path

from flask_sqlalchemy import SQLAlchemy


# Här bestämmer vi exakt var den lokala SQLite-filen ska ligga.
# main.py använder den här sökvägen när Flask kopplas till databasen.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"


# db är SQLAlchemy-objektet som Flask-appen använder för att prata med databasen.
# Det skapas här, men kopplas till Flask-appen i main.py.
db = SQLAlchemy()


# En spelare är en person som kan delta i flera olika femkamper.
# is_admin kan användas om du vill låta vissa personer fylla i resultat.
class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    game_players = db.relationship(
        "GamePlayer",
        back_populates="player",
        cascade="all, delete-orphan",
    )
    results = db.relationship(
        "Result",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


# En game är en specifik femkamp, till exempel "Midsommar 2026".
# Här sparas om femkampen fortfarande pågår eller är avslutad.
class Game(db.Model):
    __tablename__ = "game"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    occasion = db.Column(db.String(120), nullable=True)
    date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    players = db.relationship(
        "GamePlayer",
        back_populates="game",
        cascade="all, delete-orphan",
    )
    disciplines = db.relationship(
        "GameDiscipline",
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="GameDiscipline.position",
    )
    results = db.relationship(
        "Result",
        back_populates="game",
        cascade="all, delete-orphan",
    )


# En discipline är en gren, till exempel pilkastning, löpning eller quiz.
# unit beskriver resultatets enhet, till exempel "sekunder", "meter" eller "poäng".
# low_best styr om lägst resultat vinner grenen, till exempel vid tidtagning.
class Discipline(db.Model):
    __tablename__ = "disciplines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    unit = db.Column(db.String(40), nullable=True)
    low_best = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    game_disciplines = db.relationship(
        "GameDiscipline",
        back_populates="discipline",
        cascade="all, delete-orphan",
    )
    results = db.relationship(
        "Result",
        back_populates="discipline",
        cascade="all, delete-orphan",
    )


# Kopplingstabell mellan game och player.
# Den gör att samma spelare kan vara med i flera femkamper.
class GamePlayer(db.Model):
    __tablename__ = "game_players"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)

    joined_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    game = db.relationship("Game", back_populates="players")
    player = db.relationship("Player", back_populates="game_players")

    __table_args__ = (
        db.UniqueConstraint("game_id", "player_id", name="unique_game_player"),
    )


# Kopplingstabell mellan game och discipline.
# position avgör ordningen på grenarna i femkampen.
class GameDiscipline(db.Model):
    __tablename__ = "game_disciplines"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey("disciplines.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False)

    game = db.relationship("Game", back_populates="disciplines")
    discipline = db.relationship("Discipline", back_populates="game_disciplines")

    __table_args__ = (
        db.UniqueConstraint("game_id", "discipline_id", name="unique_game_discipline"),
        db.UniqueConstraint("game_id", "position", name="unique_game_discipline_position"),
    )


# Ett result är en spelares resultat i en gren i en specifik femkamp.
# value är själva resultatet, till exempel 12.5 sekunder eller 8 träffar.
# points är den uträknade poängen som används i totalställningen.
class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey("disciplines.id"), nullable=False)

    value = db.Column(db.Float, nullable=True)
    points = db.Column(db.Integer, nullable=True)
    note = db.Column(db.String(255), nullable=True)

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    game = db.relationship("Game", back_populates="results")
    player = db.relationship("Player", back_populates="results")
    discipline = db.relationship("Discipline", back_populates="results")

    __table_args__ = (
        db.UniqueConstraint(
            "game_id",
            "player_id",
            "discipline_id",
            name="unique_result_per_player_and_discipline",
        ),
    )


# Hjälpfunktion som räknar ihop totalpoängen för ett game.
# Returnerar en lista sorterad med vinnaren överst.
def get_scoreboard(game_id):
    rows = (
        db.session.query(
            Player.id.label("player_id"),
            Player.first_name,
            Player.last_name,
            db.func.coalesce(db.func.sum(Result.points), 0).label("total_points"),
        )
        .join(GamePlayer, GamePlayer.player_id == Player.id)
        .outerjoin(
            Result,
            (Result.player_id == Player.id) & (Result.game_id == GamePlayer.game_id),
        )
        .filter(GamePlayer.game_id == game_id)
        .group_by(Player.id)
        .order_by(db.desc("total_points"), Player.first_name)
        .all()
    )

    return [
        {
            "player_id": row.player_id,
            "name": f"{row.first_name} {row.last_name or ''}".strip(),
            "total_points": row.total_points,
        }
        for row in rows
    ]
