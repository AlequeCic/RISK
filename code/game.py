from objects import Player, Territory
from constants import MAP, GameState, INITIAL_ARMIES, CONTINENT_BONUS
from typing import Dict, List
import random

class Game:
    def __init__(self,map_data: dict, max_players: int = 3):
        #initialization of map, states, players and variables
        self.max_players = max_players
        self.players: Dict[int, Player] = {}
        self.territories: Dict[str, Territory] = {}
        self._territory_aliases: Dict[str, str] = {}
        #self.pack = List[Card] = {}

        #turn
        self.turn = 0
        self.current_turn_index = 0
        self.turn_order: List[int] = []

        #state
        self.current_state: str = GameState.WAITING_PLAYERS

        #colors
        self.available_colors = ["Red", "Blue", "Green", "Yellow", "Black", "Magenta"]

        self.load_map(map_data)

    #getter and setter methods
    def register_player(self, player_name) -> dict:
        #security
        if self.current_state != GameState.WAITING_PLAYERS:
            return {"error": "Game has already started"}
        
        if len(self.players) >= self.max_players:
            return {"error": "Lobby is full"}
        
        rand = random.randint(0, len(self.available_colors) - 1)
        color = self.available_colors.pop(rand)
        id = len(self.players)
        
        #player
        self.players[id] = Player(id, player_name, color, None, 0)
        return {"success": True, "player_id": id, "color": color}
    
    def load_map(self, map_data: dict):
        for name, data in map_data.items():
            self.territories[name] = Territory(
                id = data["id"],
                name = name,
                continent=data["continent"],
                neighbors=data["neighbors"],
                troops=0
            )
            self._territory_aliases[name.strip().lower()] = name

    def _canonical_territory_name(self, territory_name: str):
        if territory_name is None:
            return None
        return self._territory_aliases.get(territory_name.strip().lower())

    def start_match(self):
        player_count = len(self.players)

        #at least 1 player to play the game
        if player_count < 2:
            return{"error": "Need 2 players to start"}
        
        #assign initial troops based on player count
        starting_troops = INITIAL_ARMIES[player_count]
        for player in self.players.values():
            player.troops = starting_troops

        #setting turn order
        rolls = {}
        sorting_list = []
        for player_id in self.players.keys():
            roll = random.randint(1,6)
            rolls[player_id] = roll

            tie_breaker = random.random() #if two players tie
            sorting_list.append((roll, tie_breaker, player_id))
        #sort from highest to lowest and store it
        sorting_list.sort(reverse=True)
        self.turn_order = [item[2] for item in sorting_list]
        
        #distribute the territories
        self.distribute_initial_territories()

        # setup phase starts right after match initialization
        self.current_state = GameState.SETUP

        return {"success": True, 
                "message": "Match Started",
                "setup_rolls": rolls,
                "turn_order": self.turn_order}

    #setup and draft state (receiving and placing troops)
    def distribute_initial_territories(self):
        #get territories
        territory_names = list(self.territories.keys())
        random.shuffle(territory_names)

        #add territories
        for index, terr_name in enumerate(territory_names):

            player_id = self.turn_order[index % len(self.turn_order)]

            current_player = self.players[player_id]
            territory = self.territories[terr_name]

            territory.owner = player_id
            territory.troops = 1
            current_player.troops -= 1

    def calculate_reinforcements(self, player_id: int):
        #get player territories and base troops
        player = self.players[player_id]
        owned_territories = [t for t in self.territories.values() if t.owner == player_id]
        base_troops = max(3, len(owned_territories)//3)

        bonus_troops = 0

        for continent_name, bonus_value in CONTINENT_BONUS.items():
            
            #checks if owns all territories in a continent
            owns_a = all(
                self.territories[t_name].owner == player_id
                for t_name, t_data in MAP.items()
                if t_data["continent"] == continent_name
            )

            #if so add bonus
            if owns_a:
                bonus_troops += bonus_value

        player.troops +=(base_troops + bonus_troops)

    def _advance_setup_turn(self):
        #if it isnt your turn
        if not self.turn_order:
            return False

        #skip players that already placed all setup troops
        for _ in range(len(self.turn_order)):
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            next_player_id = self.turn_order[self.current_turn_index]
            if self.players[next_player_id].troops > 0:
                return True
        
        #gets here if everyone is with 0 troops
        return False

    def deploy_troops(self, player_id: int, territory_name: str, amount: int = 1) -> dict:
        territory_name = self._canonical_territory_name(territory_name)


        if self.current_state not in [GameState.SETUP, GameState.DRAFT]:
            return {"error": "Incorrect phase to deploy troops"}
        
        if self.turn_order[self.current_turn_index] != player_id:
            return {"error": "Not your turn"}
        
        territory = self.territories.get(territory_name)
        if not territory:
            return {"error": "Invalid territory"}
        
        if territory.owner != player_id:
            return {"error": "You don't own this territory"}
        
        player = self.players[player_id]
        if player.troops < amount:
            return {"error": "Not enough troops"}
        
        #placing the troops
        territory.troops += amount
        player.troops -= amount

        #state machine transition
        if self.current_state == GameState.SETUP:
            #try to pass turn
            has_next_player = self._advance_setup_turn()
            if not has_next_player:
                self.current_state = GameState.DRAFT
                self.current_turn_index = 0
                self.turn +=1
                self.calculate_reinforcements(self.turn_order[self.current_turn_index])

        elif self.current_state == GameState.DRAFT:
            if player.troops == 0:
                self.current_state = GameState.ATTACK
        
        return {
            "success": True,
            "territory": territory.name,
            "new_total": territory.troops,
            "troops_left": player.troops
        }


    #attack state
    def attack_territory(self, player_id: int, origin_name: str, target_name: str, dices: int, troops_to_move: int =0) -> dict:
        #validating state and turn
        if self.current_state != GameState.ATTACK:
            return {"error": "Not in attack phase"}
        if self.turn_order[self.current_turn_index] != player_id:
            return {"error" : "Not your turn"}
        
        origin_name = self._canonical_territory_name(origin_name)
        target_name = self._canonical_territory_name(target_name)

        #getting origin and target territories
        origin = self.territories.get(origin_name)
        target = self.territories.get(target_name)

        if not origin or not target:
            return {"error": "Invalid territories"}
        if origin.owner != player_id:
            return {"error": "You don't own this territory"}
        if target.owner == player_id:
            return {"error": "You can't attack your own territory"}
        if target.name not in origin.neighbors:
            return {"error": "You can only attack adjacent territories"}
        
        #validating troops and dices
        if origin.troops <=1:
            return {"error": "You need 2 troops to attack"}
        if dices < 1 or dices > 3:
            return {"error": "You can only roll between 1 and 3 dices"}
        if origin.troops <= dices:
            return {"error": f"Not enough troops to roll {dices} dices"}
        if troops_to_move < dices:
            troops_to_move = dices
        if origin.troops - troops_to_move < 1:
            return {"error": "You must leave 1 troop in the origin territory"}

        #rolling dices
        atk_rolls = sorted([random.randint(1,6) for i in range(dices)], reverse = True)

        defender_dices = 2 if target.troops >= 2 else 1
        def_rolls = sorted([random.randint(1,6) for i in range(defender_dices)], reverse=True)

        #comparing dices
        origin_losses = 0
        target_losses = 0

        comparisons = min(len(atk_rolls), len(def_rolls))

        for i in range(comparisons):
            if atk_rolls[i]> def_rolls[i]:
                target_losses+=1
            else:
                #tie or higher
                origin_losses +=1
        
        origin.troops -= origin_losses
        target.troops -= target_losses

        #checking territories
        conquered = False
        if target.troops == 0:
            conquered = True
            #old owner of the territory
            defender_id = target.owner
            target.owner = player_id
            #must move as many armies as the dice rolled
            target.troops = troops_to_move
            origin.troops -= troops_to_move

            #check elimination
            self.check_elimination(defender_id)

            #checks victory
            victory_status = self.check_victory()
            if victory_status["game_over"]:
                pass
            
        
        return {
            "success": True,
            "attacker_rolls": atk_rolls,
            "defender_rolls": def_rolls,
            "attacker_losses": origin_losses,
            "defender_losses": target_losses,
            "conquered": conquered,
            "origin_troops_left": origin.troops,
            "target_troops_left": target.troops
        }

    def end_attack(self, player_id: int)-> dict:
        #validating state and turn
        if self.current_state != GameState.ATTACK:
            return {"error": "Not in attack phase"}
        if self.turn_order[self.current_turn_index] != player_id:
            return {"error": "Not your turn"}

        self.current_state = GameState.MANEUVER

        return {
            "success": True,
            "message" : "Ended attack phase"
        } 
    
    #maneuver
    def maneuver(self, player_id: int, origin_name: str, target_name: str, amount: int) -> dict:
        #validating state and turn
        if self.current_state != GameState.MANEUVER:
            return {"error": "Not in maneuver phase"}
        if self.turn_order[self.current_turn_index] != player_id:
            return {"error": "Not your turn"}
        
        origin_name = self._canonical_territory_name(origin_name)
        target_name = self._canonical_territory_name(target_name)

        #movement and validation
        origin = self.territories.get(origin_name)
        target = self.territories.get(target_name)

        if not origin or not target:
            return {"error": "Invalid territories"}
        if origin.owner != player_id or target.owner != player_id:
            return {"error": "You must own both territories"}
        if target.name not in origin.neighbors:
            return {"error": "Territories must be neighbours"}
        if origin.troops - amount <1:
            return {"error": "You must leave 1 troop behind"}
        
        #executing the movement
        origin.troops -= amount
        target.troops += amount

        return self.end_turn(player_id)

    #end turn
    def end_turn(self, player_id: int):
        #validating turn
        if self.turn_order[self.current_turn_index] != player_id:
            return {"error": "Not your turn"}
        
        #advancing turn
        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        next_player_id = self.turn_order[self.current_turn_index]
        self.turn+=1

        #changing to draft
        self.current_state = GameState.DRAFT

        #calculating new troops
        self.calculate_reinforcements(next_player_id)

        return {
            "success": True,
            "message": "Turn ended",
            "next_player": next_player_id
        }

    #checks
    def check_elimination(self, defender_id):
        #checks if a player lost all territories

        #check how many territories a player has left
        territories_left = sum(1 for t in self.territories.values() if t.owner == defender_id)

        if territories_left == 0:
            if defender_id in self.turn_order:
                #save actual player
                active_player_id = self.turn_order[self.current_turn_index]
                #removes eliminated player
                self.turn_order.remove(defender_id)
                #update the idx using the player position in the turn order
                self.current_turn_index = self.turn_order.index(active_player_id)


    def check_victory(self) -> dict:
        
        if self.current_state in [GameState.WAITING_PLAYERS, GameState.FINISHED]:
            return {"game_over": False}
        
        #if there is only 1 player, he won
        if len(self.turn_order) == 1:
            self.current_state = GameState.FINISHED
            winner_id = self.turn_order[0]
            winner = self.players[winner_id]
        
            return {
                "game_over": True,
                "winner_id": winner.id,
                "winner_name": winner.name
            }

        return {"game_over": False}

    #sync client
    def get_player_territories(self, player_id: int) -> List[str]:
        return [
            territory.name
            for territory in self.territories.values()
            if territory.owner == player_id
        ]

    def get_player_attack_options(self, player_id: int) -> dict:
        attack_options = {}

        #gets all territories
        for territory in self.territories.values():
            #checks if the territory is from the player
            if territory.owner != player_id or territory.troops <= 1:
                continue
            
            #gets every neighbors that isnt from the player
            enemy_neighbors = [
                neighbor_name
                for neighbor_name in territory.neighbors
                if self.territories[neighbor_name].owner != player_id
            ]

            #if theres any enemy neighbors add to attack options
            if enemy_neighbors:
                attack_options[territory.name] = enemy_neighbors

        return attack_options

    def get_player_maneuver_options(self, player_id: int) -> dict:
        maneuver_options = {}

        for territory in self.territories.values():
            if territory.owner != player_id or territory.troops <= 1:
                continue

            own_neighbors = [
                neighbor_name
                for neighbor_name in territory.neighbors
                if self.territories[neighbor_name].owner == player_id
            ]

            if own_neighbors:
                maneuver_options[territory.name] = own_neighbors

        return maneuver_options

    def get_game_state(self):

        map_snap = {}
        for name, terr in self.territories.items():
            map_snap[name] = {
                "owner_id": terr.owner,
                "troops": terr.troops
            }

        player_snap  = {}
        for pid, player in self.players.items():
            player_snap[pid] = {
                "name": player.name,
                "color": player.color,
                "troops_to_place": player.troops
            }

        current_turn_id = None
        #determine safely the current turn
        if self.turn_order and self.current_state != GameState.WAITING_PLAYERS:
            current_turn_id = self.turn_order[self.current_turn_index]

        current_player_territories = []
        current_player_attack_options = {}
        current_player_maneuver_options = {}

        if current_turn_id is not None:
            current_player_territories = self.get_player_territories(current_turn_id)

            if self.current_state == GameState.ATTACK:
                current_player_attack_options = self.get_player_attack_options(current_turn_id)
            elif self.current_state == GameState.MANEUVER:
                current_player_maneuver_options = self.get_player_maneuver_options(current_turn_id)

        return {
            "current_state": self.current_state,
            "current_turn_id": current_turn_id,
            "map": map_snap,
            "players": player_snap,
            "current_player_territories": current_player_territories,
            "current_player_attack_options": current_player_attack_options,
            "current_player_maneuver_options": current_player_maneuver_options,
        }
