import os
import random
import chess
import berserk

# Cargar el token desde la variable de entorno
TOKEN = os.environ.get("LICHESS_TOKEN")

if not TOKEN:
    raise ValueError("No se encontró la variable de entorno LICHESS_TOKEN")

session = berserk.TokenSession(TOKEN)
client = berserk.Client(session=session)

# Obtener ID del bot
my_profile = client.account.get()
my_id = my_profile['id']
print(f"Bot conectado como: {my_profile['username']}")

# Escuchar eventos globales (retos, inicio de partidas)
for event in client.bots.stream_incoming_events():
    event_type = event.get('type')

    if event_type == 'challenge':
        challenge = event['challenge']
        challenge_id = challenge['id']
        variant = challenge['variant']['key']

        # Aceptar solo variantes estándar (puedes ajustar esta condición)
        if variant == 'standard':
            client.bots.accept_challenge(challenge_id)
            print(f"Reto aceptado: {challenge_id}")
        else:
            client.bots.decline_challenge(challenge_id, reason='variant')
            print(f"Reto rechazado (variante {variant}): {challenge_id}")

    elif event_type == 'gameStart':
        game_id = event['game']['gameId']
        print(f"Nueva partida iniciada: {game_id}")
        
        board = chess.Board()

        # Escuchar el flujo de la partida activa
        for game_event in client.bots.stream_game_state(game_id):
            if game_event['type'] == 'gameFull':
                white_id = game_event['white'].get('id')
                is_white = (white_id == my_id)
                state = game_event['state']
            elif game_event['type'] == 'gameState':
                state = game_event
            else:
                continue

            # Actualizar estado del tablero según los movimientos
            moves = state['moves'].split() if state['moves'] else []
            board.reset()
            for move in moves:
                board.push(chess.Move.from_uci(move))

            # Verificar si la partida terminó
            if state['status'] != 'started' or board.is_game_over():
                print(f"Partida finalizada: {game_id}")
                break

            # Verificar si es el turno del bot
            is_my_turn = (board.turn == chess.WHITE and is_white) or (board.turn == chess.BLACK and not is_white)

            if is_my_turn:
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    # Aquí puedes reemplazar la lógica de elección por tu motor/evaluación personalizada
                    chosen_move = random.choice(legal_moves)
                    client.bots.make_move(game_id, chosen_move.uci())
                    print(f"Jugada enviada [{game_id}]: {chosen_move.uci()}")
