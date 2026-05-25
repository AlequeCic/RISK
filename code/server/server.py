import Pyro5.api
from game import Game
from constants import MAP

Pyro5.api.expose(Game)
#using multiplex design (one queue to calls)
Pyro5.config.SERVERTYPE = "multiplex"

#pyro decorator "expose" to expose server class to clients
#single behavior to only exist one instance
@Pyro5.api.expose
@Pyro5.api.behavior(instance_mode="single")
class Server(Game):
    def  __init__(self):
        #instancing the game in init with 2 players and map
        super().__init__(map_data=MAP, max_players=2)

#function to start the server
def start_server():
    #prepare the server to listen on the selected port
    host = "localhost"
    port = prompt_port()

    try:
        daemon = Pyro5.api.Daemon(host=host, port=port)
    except OSError:
        print(f"Port {port} is in use.")
        return

    #register the class with a name
    #uniform resource identifier (like an url to know where the class is)
    uri = daemon.register(Server(), "risk.server")

    print("="*50)
    print("SERVIDOR DE RISK INICIADO COM SUCESSO!")
    print(f"Endereco: PYRO:risk.server@{host}:{port}")
    print("="*50)

    #
    daemon.requestLoop()


def prompt_port(default_port=9090):
    while True:
        raw = input(f"Qual porta deseja usar? (Enter para {default_port}): ").strip()
        if not raw:
            return default_port

        try:
            port = int(raw)
        except ValueError:
            print("Porta invalida. Digite um numero inteiro.")
            continue

        if 1 <= port <= 65535:
            return port

        print("Porta invalida. Use um valor entre 1 e 65535.")

if __name__ == "__main__":
    start_server()