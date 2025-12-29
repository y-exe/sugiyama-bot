# engines/othello.py
import datetime
from core.constants import EMPTY, BLACK, WHITE, MARKERS

class OthelloEngine:
    _next_game_id_counter = 1

    def __init__(self, board_size: int = 8):
        self.board_size = board_size
        self.board = [[EMPTY]*board_size for _ in range(board_size)]
        
        mid_l, mid_h = board_size // 2 - 1, board_size // 2
        self.board[mid_l][mid_l], self.board[mid_l][mid_h] = WHITE, BLACK
        self.board[mid_h][mid_l], self.board[mid_h][mid_h] = BLACK, WHITE
        
        self.current_player = BLACK
        self.valid_moves_with_markers = {}
        self.game_over = False
        self.winner = None
        self.last_pass = False
        self.last_move_time = datetime.datetime.now()
        
        self.players = {} # {BLACK: id, WHITE: id}
        self.channel_id = None
        self.message_id = None
        self.afk_task = None
        
        self.game_id = OthelloEngine._assign_game_id_static()

    @staticmethod
    def _assign_game_id_static():
        gid = OthelloEngine._next_game_id_counter
        OthelloEngine._next_game_id_counter += 1
        return gid

    def is_on_board(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def get_flips(self, r_s, c_s, p):
        if not self.is_on_board(r_s, c_s) or self.board[r_s][c_s] != EMPTY:
            return []
        op = WHITE if p == BLACK else BLACK
        ttf = []
        for dr, dc in [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]:
            r, c = r_s + dr, c_s + dc
            cpf = []
            while self.is_on_board(r, c) and self.board[r][c] == op:
                cpf.append((r, c))
                r, c = r + dr, c + dc
            if self.is_on_board(r, c) and self.board[r][c] == p and cpf:
                ttf.extend(cpf)
        return ttf

    def calculate_valid_moves(self, p):
        self.valid_moves_with_markers.clear()
        mi = 0
        cvc = []
        for r_idx in range(self.board_size):
            for c_idx in range(self.board_size):
                if self.board[r_idx][c_idx] == EMPTY and self.get_flips(r_idx, c_idx, p): 
                    cvc.append((r_idx, c_idx))
                    self.valid_moves_with_markers[(r_idx, c_idx)] = MARKERS[mi] if mi < len(MARKERS) else "❓"
                    mi += 1
        return cvc

    def make_move(self, r, c, p):
        if self.game_over or not self.is_on_board(r, c) or self.board[r][c] != EMPTY:
            return False
        ttf = self.get_flips(r, c, p)
        if not ttf:
            return False
        self.board[r][c] = p
        for fr_loop, fc_loop in ttf:
            self.board[fr_loop][fc_loop] = p
        self.last_pass = False
        self.last_move_time = datetime.datetime.now()
        return True

    def switch_player(self):
        self.current_player = WHITE if self.current_player == BLACK else BLACK

    def check_game_status(self):
        if self.game_over: return
        if self.calculate_valid_moves(self.current_player):
            self.last_pass = False
            return
        if self.last_pass:
            self.game_over = True
        else:
            self.last_pass = True
            self.switch_player()
            if not self.calculate_valid_moves(self.current_player):
                self.game_over = True
        
        if self.game_over:
            self.determine_winner()

    def determine_winner(self):
        bs = sum(r.count(BLACK) for r in self.board)
        ws = sum(r.count(WHITE) for r in self.board)
        if bs > ws: self.winner = BLACK
        elif ws > bs: self.winner = WHITE
        else: self.winner = EMPTY

    def get_current_player_id(self):
        return self.players.get(self.current_player)