import time
import Pyro5.api
from constants import GameState

try:
    from .clientui import (
        clear_screen, format_owned_territories, get_player_snapshot,
        print_phase_header, print_player_status, print_player_cards,
        print_waiting_summary, prompt_card_indices, prompt_choice,
        prompt_positive_int, prompt_territory
    )
except ImportError:
    from clientui import (
        clear_screen, format_owned_territories, get_player_snapshot,
        print_phase_header, print_player_status, print_player_cards,
        print_waiting_summary, prompt_card_indices, prompt_choice,
        prompt_positive_int, prompt_territory
    )


def init_client():
    # connection
    clear_screen()
    print("=" * 40)
    print(" WELCOME TO RISK (MULTIPLAYER) ")
    print("=" * 40)

    # server address
    ip = input("Enter the server IP (press Enter for localhost): ").strip()
    if not ip:
        ip = "localhost"

    port = input("Enter the server port (press Enter for 9090): ").strip()
    if not port:
        port = "9090"

    uri = f"PYRO:risk.server@{ip}:{port}"

    print(f"\nConnecting to server at {uri}...")
    game = None
    try:
        game = Pyro5.api.Proxy(uri)
        game.get_game_state()
    except Exception:
        print("Connection error: Could not reach the server.")
        print("Check whether the IP and port are correct and the server is running.")
        return

    # player registration
    name = input("Enter your nickname: ").strip()
    result = game.register_player(name)

    if "error" in result:
        print(f"Join error: {result['error']}")
        return

    my_id = result["player_id"]
    print(f"Registered successfully. You are Player {my_id} ({result['color']}).")

    # main loop
    last_phase = None
    turn_waited_message = False
    last_event_seen = None
    registered = True

    try:
        while True:
            state = game.get_game_state()
            current_phase = state["current_state"]
            turn_id = state["current_turn_id"]
            turn_name = state.get("current_turn_player_name")
            player_state = get_player_snapshot(state["players"], turn_id)
            last_event = state.get("last_event")
            my_state = game.get_player_state(my_id)

            # show the latest action once for every client
            if last_event and last_event != last_event_seen:
                last_event_seen = last_event
                print(f"\nLast action: {last_event['message']}")

            if current_phase == GameState.WAITING_PLAYERS:
                if my_id == 1:
                    print("You are the last player. Starting the match...")
                    game.start_match()
                    time.sleep(1)
                else:
                    print("Waiting for more players...", end="\r")
                    time.sleep(1)
                continue

            if current_phase == GameState.FINISHED:
                clear_screen()
                print("\n" + "=" * 40)
                print(" GAME OVER ")
                print("=" * 40)
                victory = state.get("victory") or {}
                if victory.get("game_over"):
                    winner_name = victory.get("winner_name")
                    print(f"Winner: {winner_name}")
                else:
                    print("Check the server for the winner.")
                break # SAI DO LOOP E VAI PARA O FINALLY

            # refresh on phase change
            if current_phase != last_phase:
                clear_screen()
                last_phase = current_phase
                turn_waited_message = False

            if turn_id != my_id:
                # keep non-active players in sync with the current turn
                if not turn_waited_message:
                    if turn_name:
                        print(f"\nPhase: {current_phase} | Waiting for Player {turn_id} ({turn_name}) to act...")
                    else:
                        print(f"\nPhase: {current_phase} | Waiting for Player {turn_id} to act...")
                    turn_waited_message = True

                    # show a nicer waiting/summary view for non-active players
                    print_waiting_summary(my_state, state)
                time.sleep(1)
                continue

            # active turn
            turn_waited_message = False

            print_phase_header(current_phase, turn_id, turn_name)
            print("It is your turn.")

            # format the action result in plain text
            def print_action_result(result, success_text):
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(success_text)

            match current_phase:
                case GameState.SETUP:
                    print(f"Troops to place: {player_state['troops_to_place']}")
                    print(f"Your territories: {', '.join(state['current_player_territories'])}")
                    terr = prompt_territory(
                        "Enter the territory name to place 1 troop: ",
                        state["current_player_territories"],
                    )
                    result = game.deploy_troops(turn_id, terr)
                    print_action_result(
                        result,
                        f"Troop placed in {result.get('territory')}. Troops left to place: {result.get('troops_left')}."
                    )

                case GameState.DRAFT:
                    troops_to_place = player_state['troops_to_place']
                    print(f"Troops to place: {troops_to_place}")
                    print(f"Your territories: {', '.join(state['current_player_territories'])}")
                    print_player_cards(state["current_player_cards"])

                    action = prompt_choice(
                        "Type 1 to place troops\nType 2 to trade cards\n",
                        {1, 2},
                    )

                    if action == 2:
                        if len(state["current_player_cards"]) < 3:
                            print("You need at least 3 cards to trade.")
                            input("Press Enter to continue...")
                            continue

                        print("Choose exactly 3 cards by their indices shown above.")
                        card_indices = prompt_card_indices("Cards to trade: ")
                        result = game.trade_cards(turn_id, card_indices)
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        else:
                            bonus_text = (
                                f" Bonus territory: {result['bonus_territory']}." if result.get("bonus_territory") else ""
                            )
                            print(
                                f"Cards traded successfully. You gained {result['troops_gained']} troops.{bonus_text}"
                            )
                        input("Press Enter to continue...")
                        continue

                    terr = prompt_territory(
                        "Enter the territory name to place troops: ",
                        state["current_player_territories"],
                    )
                    amount = prompt_positive_int(
                        "Enter the number of troops you want to place: ",
                        min_value=1,
                        max_value=troops_to_place,
                    )

                    result = game.deploy_troops(turn_id, terr, amount)
                    print_action_result(
                        result,
                        f"Placed {amount} troops in {result.get('territory')}. Troops left to place: {result.get('troops_left')}."
                    )

                case GameState.ATTACK:
                    options = state["current_player_attack_options"]
                    print(f"Your territories: {format_owned_territories(state, turn_id)}")

                    if options:
                        print("Attack options:")
                        for origin, targets in options.items():
                            print(f"  {origin} -> {', '.join(targets)}")
                    else:
                        print("No valid attacks are available. You need 2+ troops and an enemy neighbor.")
                        result = game.end_attack(turn_id)
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        else:
                            print("Attack phase ended.")
                        input("Press Enter to continue to maneuver phase...")
                        continue

                    action = prompt_choice(
                        "Type 1 to attack\nType 2 to pass your turn\n",
                        {1, 2},
                    )
                    if action == 2:
                        result = game.end_attack(turn_id)
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        else:
                            print("Attack phase ended.")
                        input("Press Enter to continue to maneuver phase...")
                    else:
                        origin = prompt_territory(
                            "Enter the origin territory name: ",
                            list(options.keys()),
                        )
                        target = prompt_territory(
                            "Enter the target territory name: ",
                            options[origin],
                        )

                        max_dice = min(3, state["map"][origin]["troops"] - 1)
                        dice_qnt = prompt_positive_int(
                            "Enter the dice count: ",
                            min_value=1,
                            max_value=max_dice,
                        )
                        result = game.attack_territory(turn_id, origin, target, dice_qnt)
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        else:
                            outcome = (
                                "You conquered the territory."
                                if result.get("conquered")
                                else "Attack resolved."
                            )
                            print(
                                f"{outcome} Attacker losses: {result['attacker_losses']}. Defender losses: {result['defender_losses']}."
                            )
                        input("Press Enter to continue...")

                case GameState.MANEUVER:
                    print(f"Your territories: {format_owned_territories(state, turn_id)}")
                    maneuver_options = state["current_player_maneuver_options"]

                    if maneuver_options:
                        print("Maneuver options (origin -> allied neighbor territories):")
                        for origin, targets in maneuver_options.items():
                            print(f"  {origin} -> {', '.join(targets)}")
                    else:
                        print("No valid maneuvers are available. You need 2+ troops and an allied neighbor.")
                        result = game.end_turn(turn_id)
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        else:
                            print("Turn ended.")
                        input("Press Enter to pass the turn to the next player...")
                        continue

                    action = prompt_choice(
                        "Type 1 to move troops\nType 2 to pass your turn\n",
                        {1, 2},
                    )

                    if action == 2:
                        result = game.end_turn(turn_id)
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        else:
                            card_text = f" Card earned: {result['card_earned']}." if result.get("card_earned") else ""
                            print(f"Turn ended. Next player: {result['next_player']}.{card_text}")
                        input("Press Enter to end turn...")

                    else:
                        origin = prompt_territory(
                            "Enter the origin territory name: ",
                            list(maneuver_options.keys()),
                        )
                        target = prompt_territory(
                            "Enter the target territory name: ",
                            maneuver_options[origin],
                        )

                        max_troops_to_move = state["map"][origin]["troops"] - 1
                        troop_qnt = prompt_positive_int(
                            "Enter the troop count: ",
                            min_value=1,
                            max_value=max_troops_to_move,
                        )

                        result = game.maneuver(turn_id, origin, target, troop_qnt)
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        else:
                            card_text = f" Card earned: {result['card_earned']}." if result.get("card_earned") else ""
                            print(f"Troops moved. Next player: {result['next_player']}.{card_text}")
                        input("Press Enter to pass the turn to the next player...")
    finally:
        try:
            if registered:
                game.unregister_player(my_id)
        except Exception:
            pass


if __name__ == "__main__":
    init_client()