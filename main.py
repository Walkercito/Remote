import sys
import pygame
import socket
import json
import threading
from config import (
    WIDTH,
    HEIGHT,
    WHITE,
    MAX_GAMETAG_LENGHT
)
from src.player import Player


class NetworkClient:
    def __init__(self, host: str = 'localhost', port: int = 12345):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.running = True
        
        
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            return False
    

    def send_message(self, message: dict):
        if self.connected:
            try:
                message_str = json.dumps(message) + '\n'
                self.socket.send(message_str.encode('utf-8'))
            except Exception as e:
                self.connected = False
    

    def listen_for_messages(self, game):
        buffer = ""
        
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            message = json.loads(line.strip())
                            game.process_network_message(message)
                        except json.JSONDecodeError:
                            pass
                            
            except Exception as e:
                break
        
        self.connected = False
    

    def disconnect(self):
        self.running = False
        self.connected = False
        try:
            self.socket.close()
        except:
            pass


class Game:
    def __init__(self, gametag: str):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"Remote - Multiplayer ({gametag})")
        self.clock = pygame.time.Clock()
        
        self.network_client = NetworkClient()
        
        self.local_player = None
        self.gametag = gametag
        
        self.remote_players = {}
        
        self.connected = False
    
        self.font = pygame.font.SysFont(None, 36)
    

    def connect_to_server(self):
        if self.network_client.connect():
            self.connected = True
            
            listen_thread = threading.Thread(
                target=self.network_client.listen_for_messages,
                args=(self,)
            )
            listen_thread.daemon = True
            listen_thread.start()
            
            join_message = {
                'type': 'join',
                'gametag': self.gametag
            }
            self.network_client.send_message(join_message)


    def process_network_message(self, message: dict):
        msg_type = message.get('type')
        
        if msg_type == 'join_response':
            color = tuple(message.get('color', (255, 0, 0)))
            x_pos = message.get('x_pos', 100)
            y_pos = message.get('y_pos', 100)
            
            self.local_player = Player(x_pos, y_pos, 50, color, self.gametag)
        
        elif msg_type == 'game_state':
            players = message.get('players', [])
            for player_data in players:
                gametag = player_data['gametag']
                if gametag != self.gametag:
                    color = tuple(player_data['color'])
                    x_pos = player_data['x_pos']
                    y_pos = player_data['y_pos']
                    
                    self.remote_players[gametag] = Player(x_pos, y_pos, 50, color, gametag)
        
        elif msg_type == 'player_joined':
            gametag = message.get('gametag')
            if gametag != self.gametag:
                color = tuple(message.get('color', (255, 0, 0)))
                x_pos = message.get('x_pos', 100)
                y_pos = message.get('y_pos', 100)
                
                self.remote_players[gametag] = Player(x_pos, y_pos, 50, color, gametag)
        
        elif msg_type == 'player_moved':
            gametag = message.get('gametag')
            if gametag in self.remote_players:
                self.remote_players[gametag].x_pos = message.get('x_pos', 0)
                self.remote_players[gametag].y_pos = message.get('y_pos', 0)
        
        elif msg_type == 'player_left':
            gametag = message.get('gametag')
            if gametag in self.remote_players:
                del self.remote_players[gametag]


    def send_position_update(self):
        if self.connected and self.local_player:
            position_update = {
                'type': 'position_update',
                'x_pos': self.local_player.x_pos,
                'y_pos': self.local_player.y_pos
            }
            self.network_client.send_message(position_update)


    def update(self):
        delta_time = self.clock.tick(60) / 1000
        keys = pygame.key.get_pressed()
        
        # Updates
        if self.connected and self.local_player:
            old_x, old_y = self.local_player.x_pos, self.local_player.y_pos
            self.local_player.update(keys, delta_time)
            
            if (abs(self.local_player.x_pos - old_x) > 0.1 or 
                abs(self.local_player.y_pos - old_y) > 0.1):
                self.send_position_update()
        
        # Draw
        self.screen.fill(WHITE)
        
        if not self.connected:
            text = self.font.render("Connecting to server...", True, (255, 0, 0))
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(text, text_rect)
        else:
            if self.local_player:
                self.local_player.render(self.screen)
            
            for remote_player in self.remote_players.values():
                remote_player.render(self.screen)
            
            info_text = f"Players connected: {len(self.remote_players) + (1 if self.local_player else 0)}"
            text_surface = pygame.font.SysFont(None, 24).render(info_text, True, (0, 0, 0))
            self.screen.blit(text_surface, (10, 10))
        
        pygame.display.flip()


    def run(self):
        self.connect_to_server()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.network_client.disconnect()
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and not self.connected:
                        self.connect_to_server()
            
            self.update()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        gametag = sys.argv[1]
    else:
        gametag = str(input("Gametag: ")).strip()
        
        while len(gametag) > MAX_GAMETAG_LENGHT or len(gametag) == 0:
            print(f"Gametag must be between 1 and {MAX_GAMETAG_LENGHT} characters.")
            gametag = str(input("Gametag: ")).strip()
    
    game = Game(gametag)
    game.run()