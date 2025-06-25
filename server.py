import socket
import threading
import json
import random
from typing import Dict, List, Tuple
from rich.console import Console
from rich.text import Text

console = Console()



class GameServer:
    def __init__(self, host: str = 'localhost', port: int = 12345):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.players: Dict[socket.socket, dict] = {}
        self.running = True
        
        self.available_colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255),
            (0, 255, 255), (255, 165, 0), (128, 0, 128), (255, 192, 203), (0, 128, 0)
        ]


    def get_random_color(self) -> Tuple[int, int, int]:
        return random.choice(self.available_colors)


    def get_random_spawn_position(self) -> Tuple[float, float]:
        x = random.randint(50, 1030)
        y = random.randint(50, 670)
        return float(x), float(y)

    
    def broadcast_to_all(self, message: dict, exclude_client: socket.socket = None):
        message_str = json.dumps(message) + '\n'
        disconnected_clients = []
        
        for client_socket in self.players.keys():
            if client_socket != exclude_client:
                try:
                    client_socket.send(message_str.encode('utf-8'))
                except:
                    disconnected_clients.append(client_socket)
        
        for client in disconnected_clients:
            self.remove_player(client)


    def send_game_state(self, client_socket: socket.socket):
        players_data = []
        for player_info in self.players.values():
            players_data.append({
                'gametag': player_info['gametag'],
                'x_pos': player_info['x_pos'],
                'y_pos': player_info['y_pos'],
                'color': player_info['color']
            })
        
        game_state = {
            'type': 'game_state',
            'players': players_data
        }
        
        try:
            message = json.dumps(game_state) + '\n'
            client_socket.send(message.encode('utf-8'))
        except:
            self.remove_player(client_socket)


    def handle_client(self, client_socket: socket.socket, address):
        try:
            buffer = ""
            
            while self.running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            message = json.loads(line.strip())
                            self.process_message(client_socket, message)
                        except json.JSONDecodeError:
                            pass
                
        except Exception as e:
            pass
        finally:
            self.remove_player(client_socket)
            client_socket.close()


    def process_message(self, client_socket: socket.socket, message: dict):
        msg_type = message.get('type')
        
        if msg_type == 'join':
            gametag = message.get('gametag', 'Player')
            color = self.get_random_color()
            x_pos, y_pos = self.get_random_spawn_position()
            
            self.players[client_socket] = {
                'gametag': gametag,
                'x_pos': x_pos,
                'y_pos': y_pos,
                'color': color
            }
            
            response = {
                'type': 'join_response',
                'color': color,
                'x_pos': x_pos,
                'y_pos': y_pos
            }
            client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
            
            player_joined = {
                'type': 'player_joined',
                'gametag': gametag,
                'x_pos': x_pos,
                'y_pos': y_pos,
                'color': color
            }
            self.broadcast_to_all(player_joined, exclude_client=client_socket)
            
            self.send_game_state(client_socket)
            
            text = Text()
            text.append("[ + ] New player ", style="green")
            text.append(gametag, style="bold cyan")
            console.print(text)
        
        elif msg_type == 'position_update':
            if client_socket in self.players:
                self.players[client_socket]['x_pos'] = message.get('x_pos', 0)
                self.players[client_socket]['y_pos'] = message.get('y_pos', 0)
                
                update_message = {
                    'type': 'player_moved',
                    'gametag': self.players[client_socket]['gametag'],
                    'x_pos': message.get('x_pos', 0),
                    'y_pos': message.get('y_pos', 0)
                }
                self.broadcast_to_all(update_message, exclude_client=client_socket)


    def remove_player(self, client_socket: socket.socket):
        if client_socket in self.players:
            gametag = self.players[client_socket]['gametag']
            del self.players[client_socket]
            
            player_left = {
                'type': 'player_left',
                'gametag': gametag
            }
            self.broadcast_to_all(player_left)
            
            text = Text()
            text.append("[ - ] Player left ", style="red")
            text.append(gametag, style="bold cyan")
            console.print(text)


    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            console.print(f"[bold green]Server started on {self.host}:{self.port}[/bold green]")
            console.print("[yellow]Waiting for connections...[/yellow]")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except OSError:
                    break
                    
        except Exception as e:
            console.print(f"[red]Server error: {e}[/red]")
        finally:
            self.stop()
    
    def stop(self):
        self.running = False
        self.socket.close()



if __name__ == "__main__":
    server = GameServer()
    try:
        server.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping server...[/yellow]")
        server.stop()