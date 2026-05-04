from datetime import date

from main import app
from database import (
    db,
    Discipline,
    Game,
    GameDiscipline,
    GamePlayer,
    Player,
    Result,
)
from routes import build_game_results


SAMPLE_GAME_NAME = "Sample Game"


def get_or_create_discipline(name, unit, low_best):
    # Grenar har unique=True på name, så vi återanvänder befintliga grenar
    # istället för att skapa dubletter varje gång scriptet körs.
    discipline = Discipline.query.filter_by(name=name).first()

    if discipline:
        discipline.unit = unit
        discipline.low_best = low_best
        return discipline

    discipline = Discipline(name=name, unit=unit, low_best=low_best)
    db.session.add(discipline)
    return discipline


def get_or_create_player(first_name):
    # Sample-spelarna återanvänds om de redan finns.
    # Det gör att scriptet kan köras flera gånger utan att skapa nya Player1 varje gång.
    player = Player.query.filter_by(first_name=first_name, last_name=None).first()

    if player:
        player.is_admin = False
        return player

    player = Player(first_name=first_name)
    db.session.add(player)
    return player


def create_sample_data():
    # Säkerställ att tabellerna finns innan vi börjar lägga in testdata.
    db.create_all()

    # Ta bort tidigare sample-game så scriptet kan köras flera gånger
    # utan att skapa flera likadana spel.
    old_game = Game.query.filter_by(name=SAMPLE_GAME_NAME).first()
    if old_game:
        db.session.delete(old_game)
        db.session.commit()

    game = Game(
        name=SAMPLE_GAME_NAME,
        occasion="Testdata",
        date=date.today(),
        is_active=True,
    )
    db.session.add(game)

    players = [
        get_or_create_player("Player1"),
        get_or_create_player("Player2"),
        get_or_create_player("Player3"),
        get_or_create_player("Player4"),
        get_or_create_player("Player5"),
    ]

    disciplines = [
        get_or_create_discipline("Pil", "poäng", False),
        get_or_create_discipline("Löpning", "sekunder", True),
        get_or_create_discipline("Kast", "meter", False),
        get_or_create_discipline("Quiz", "poäng", False),
        get_or_create_discipline("Balans", "sekunder", False),
    ]

    db.session.flush()

    for player in players:
        db.session.add(GamePlayer(game_id=game.id, player_id=player.id))

    for position, discipline in enumerate(disciplines, start=1):
        db.session.add(
            GameDiscipline(
                game_id=game.id,
                discipline_id=discipline.id,
                position=position,
            )
        )

    # Varje lista innehåller fem resultat, ett per spelare i ordningen ovan.
    # points är redan uträknade så scoreboarden kan visas direkt.
    sample_results = {
        "Pil": [(42, 5), (38, 3), (44, 6), (35, 2), (40, 4)],
        "Löpning": [(13.8, 4), (12.9, 6), (14.4, 3), (15.1, 2), (13.2, 5)],
        "Kast": [(7.2, 3), (8.1, 5), (6.8, 2), (8.7, 6), (7.9, 4)],
        "Quiz": [(8, 5), (6, 3), (9, 6), (5, 2), (7, 4)],
        "Balans": [(31, 4), (28, 3), (35, 6), (24, 2), (33, 5)],
    }

    for discipline in disciplines:
        for player, (value, points) in zip(players, sample_results[discipline.name]):
            db.session.add(
                Result(
                    game_id=game.id,
                    player_id=player.id,
                    discipline_id=discipline.id,
                    value=value,
                    points=points,
                    note="Sample data",
                )
            )

    db.session.commit()
    return game


if __name__ == "__main__":
    with app.app_context():
        sample_game = create_sample_data()
        game_results = build_game_results(sample_game)

        print(f"Created sample game: {sample_game.name} (id: {sample_game.id})")
        print("Scoreboard:")
        for row in game_results["players"]:
            print(
                f"{row['total_place']}. "
                f"{row['player_name']} - "
                f"{row['total_rank_score']} placeringspoäng"
            )
