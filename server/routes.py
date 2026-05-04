from flask import Blueprint, jsonify

from database import (
    db,
    Discipline,
    Game,
    GameDiscipline,
    GamePlayer,
    Player,
    Result,
)


routes = Blueprint("routes", __name__)


def format_date(value):
    if value is None:
        return None
    return value.isoformat()


def format_player_name(player):
    if player.last_name:
        return f"{player.first_name} {player.last_name}"
    return player.first_name


def calculate_ranks(rows, low_best):
    # rows är en lista med dictar som minst innehåller value.
    # Om low_best=True är lägst resultat bäst, till exempel vid tid.
    completed_rows = [row for row in rows if row["value"] is not None]
    completed_rows.sort(key=lambda row: row["value"], reverse=not low_best)

    last_value = None
    last_rank = None
    for index, row in enumerate(completed_rows, start=1):
        if last_value is None or row["value"] != last_value:
            last_rank = index
            last_value = row["value"]
        row["rank"] = last_rank

    for row in rows:
        if row["value"] is None:
            row["rank"] = None


def build_game_results(game):
    disciplines = (
        db.session.query(Discipline, GameDiscipline.position)
        .join(GameDiscipline, GameDiscipline.discipline_id == Discipline.id)
        .filter(GameDiscipline.game_id == game.id)
        .order_by(GameDiscipline.position)
        .all()
    )
    players = (
        Player.query.join(GamePlayer, GamePlayer.player_id == Player.id)
        .filter(GamePlayer.game_id == game.id)
        .order_by(Player.first_name, Player.last_name)
        .all()
    )
    results = Result.query.filter_by(game_id=game.id).all()

    result_by_player_and_discipline = {
        (result.player_id, result.discipline_id): result
        for result in results
    }
    player_rows = {
        player.id: {
            "player_id": player.id,
            "player_name": format_player_name(player),
            "disciplines": {},
            "total_rank_score": 0,
            "completed_disciplines": 0,
            "total_place": None,
        }
        for player in players
    }

    discipline_payload = []
    for discipline, position in disciplines:
        discipline_payload.append(
            {
                "id": discipline.id,
                "name": discipline.name,
                "unit": discipline.unit,
                "low_best": discipline.low_best,
                "position": position,
            }
        )

        discipline_rows = []
        for player in players:
            result = result_by_player_and_discipline.get((player.id, discipline.id))
            row = {
                "player_id": player.id,
                "value": result.value if result else None,
                "unit": discipline.unit,
                "rank": None,
            }
            discipline_rows.append(row)

        calculate_ranks(discipline_rows, discipline.low_best)

        for row in discipline_rows:
            player_row = player_rows[row["player_id"]]
            player_row["disciplines"][str(discipline.id)] = {
                "value": row["value"],
                "unit": row["unit"],
                "rank": row["rank"],
            }

            if row["rank"] is not None:
                player_row["total_rank_score"] += row["rank"]
                player_row["completed_disciplines"] += 1

    ranked_players = list(player_rows.values())
    discipline_count = len(discipline_payload)
    for player_row in ranked_players:
        if player_row["completed_disciplines"] != discipline_count:
            player_row["total_rank_score"] = None

    total_rank_rows = [
        {
            "value": player_row["total_rank_score"],
            "player_row": player_row,
        }
        for player_row in ranked_players
    ]
    calculate_ranks(total_rank_rows, low_best=True)

    for row in total_rank_rows:
        row["player_row"]["total_place"] = row["rank"]

    ranked_players.sort(
        key=lambda player_row: (
            player_row["total_place"] if player_row["total_place"] is not None else 999,
            player_row["player_name"],
        )
    )

    return {
        "id": game.id,
        "name": game.name,
        "occasion": game.occasion,
        "date": format_date(game.date),
        "is_active": game.is_active,
        "disciplines": discipline_payload,
        "players": ranked_players,
    }


@routes.get("/api/health")
def health_check():
    return jsonify({"status": "ok"})


@routes.get("/api/game")
def list_game():
    games = Game.query.order_by(Game.date.desc(), Game.created_at.desc()).all()

    return jsonify(
        [
            {
                "id": game.id,
                "name": game.name,
                "occasion": game.occasion,
                "date": format_date(game.date),
                "is_active": game.is_active,
            }
            for game in games
        ]
    )


@routes.get("/api/players")
def list_players():
    players = Player.query.order_by(Player.first_name, Player.last_name).all()

    return jsonify(
        [
            {
                "id": player.id,
                "first_name": player.first_name,
                "last_name": player.last_name,
                "name": format_player_name(player),
                "is_admin": player.is_admin,
            }
            for player in players
        ]
    )


@routes.get("/api/disciplines")
def list_disciplines():
    disciplines = Discipline.query.order_by(Discipline.name).all()

    return jsonify(
        [
            {
                "id": discipline.id,
                "name": discipline.name,
                "unit": discipline.unit,
                "low_best": discipline.low_best,
            }
            for discipline in disciplines
        ]
    )


@routes.get("/api/game-results")
def list_all_game_results():
    games = Game.query.order_by(Game.date.desc(), Game.created_at.desc()).all()
    return jsonify([build_game_results(game) for game in games])


@routes.get("/api/game/<int:game_id>/results")
def game_results(game_id):
    game = Game.query.get_or_404(game_id)
    return jsonify(build_game_results(game))


@routes.get("/api/game/<int:game_id>/scoreboard")
def scoreboard(game_id):
    game = Game.query.get_or_404(game_id)
    game_result = build_game_results(game)

    return jsonify(
        [
            {
                "player_id": player["player_id"],
                "name": player["player_name"],
                "total_rank_score": player["total_rank_score"],
                "total_place": player["total_place"],
            }
            for player in game_result["players"]
        ]
    )
