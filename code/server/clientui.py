import os


# screen helpers
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# display helpers
def format_owned_territories(state, player_id=None):
    territories = state["current_player_territories"]
    if not territories:
        return "None"

    return ", ".join(
        f"{name} ({state['map'][name]['troops']} troops)"
        for name in territories
    )


def format_card(card):
    territory = card["territory"] if card["territory"] else "Wildcard"
    symbol = card["symbol"].replace("_", " ").title()
    return f"[{card['index']}] {symbol} - {territory}"


def print_player_cards(cards):
    print("Your cards:")
    if not cards:
        print("  None")
        return

    print("  +-------------------------------+")
    for card in cards:
        print(f"  | {format_card(card):<29}|")
    print("  +-------------------------------+")


# prompt helpers
def prompt_card_indices(prompt_text):
    while True:
        raw = input(prompt_text).strip()
        if not raw:
            print("Type three card indices separated by commas.")
            continue

        parts = [part.strip() for part in raw.split(",") if part.strip()]
        try:
            indices = [int(part) for part in parts]
        except ValueError:
            print("Invalid cards. Use numbers separated by commas, for example: 0,1,2")
            continue

        return indices


def prompt_choice(prompt_text, valid_values):
    while True:
        raw = input(prompt_text).strip()
        try:
            value = int(raw)
        except ValueError:
            print("Invalid option. Type a number.")
            continue

        if value not in valid_values:
            print(f"Invalid option. Valid options: {sorted(valid_values)}")
            continue

        return value


def prompt_positive_int(prompt_text, min_value=1, max_value=None):
    while True:
        raw = input(prompt_text).strip()
        try:
            value = int(raw)
        except ValueError:
            print("Invalid number.")
            continue

        if value < min_value:
            print(f"Value must be at least {min_value}.")
            continue

        if max_value is not None and value > max_value:
            print(f"Value must be at most {max_value}.")
            continue

        return value


def prompt_territory(prompt_text, valid_territories=None):
    while True:
        raw = input(prompt_text).strip()

        if not raw:
            print("Invalid territory name.")
            continue

        if valid_territories is not None:
            valid_lookup = {name.lower(): name for name in valid_territories}
            canonical_name = valid_lookup.get(raw.lower())
            if not canonical_name:
                print(f"Territory not valid in this context. Valid: {', '.join(valid_territories)}")
                continue
            return canonical_name

        return raw


# state helpers
def get_player_snapshot(players, player_id):
    return players.get(player_id) or players.get(str(player_id))


def print_phase_header(current_phase, turn_id, turn_name=None):
    #show the active phase and the player responsible for it
    print("\n" + "=" * 40)
    if turn_name:
        print(f"Phase: {current_phase} | Player turn: {turn_id} ({turn_name})")
    else:
        print(f"Phase: {current_phase} | Player turn: {turn_id}")
    print("=" * 40)


def print_player_status(status):
    print(f"Player status: {status['name']} ({status['color']})")
    print(f"Troops to place: {status['troops_to_place']}")
    print(f"Territory count: {status['territory_count']}")

    if status["territories"]:
        print("Territories:")
        for territory in status["territories"]:
            print(f"  {territory['name']} - {territory['troops']} troops")
    else:
        print("Territories: none")

    if status["cards"]:
        print("Cards:")
        for card in status["cards"]:
            territory = card["territory"] if card["territory"] else "Wildcard"
            print(f"  [{card['index']}] {card['symbol']} - {territory}")
    else:
        print("Cards: none")

    if status["continents"]:
        print("Fully owned continents: " + ", ".join(status["continents"]))
    else:
        print("Fully owned continents: none")


def print_waiting_summary(my_state, game_state, width: int = 72):
    """Clear the screen and render a compact, readable waiting/summary view.

    Shows: current active player, last shared event, player's quick stats,
    territory list and cards in a tidy boxed layout.
    """
    clear_screen()
    current_turn = game_state.get("current_turn_player_name") or f"Player {game_state.get('current_turn_id', '?')}"
    last_event = game_state.get("last_event")

    sep = "=" * width
    sub = "-" * width

    print(sep)
    title = f" Waiting — Current turn: {current_turn} "
    print(title.center(width))
    print(sep)

    if last_event and isinstance(last_event, dict):
        evt = last_event.get("message")
        if evt:
            print(f"Last action: {evt}")
    print(sub)

    # player summary header
    print(f"Player: {my_state.get('name')} ({my_state.get('color')})")
    print(f"Troops to place: {my_state.get('troops_to_place')}  |  Territories: {my_state.get('territory_count')}  |  Cards: {my_state.get('card_count')}")
    print()

    # territories in a simple list with troops aligned
    print("Territories:")
    territories = my_state.get("territories") or []
    if territories:
        for t in territories:
            name = t.get("name")
            troops = t.get("troops")
            print(f"  - {name:<35} {troops:>3} troops")
    else:
        print("  None")

    print()
    # cards
    cards = my_state.get("cards") or []
    if cards:
        print("Cards:")
        # reuse the existing formatter for consistency
        print_player_cards(cards)
    else:
        print("Cards: none")

    print(sub)
    print("Waiting... the screen will refresh automatically when the game state updates.")
    print(sep)
