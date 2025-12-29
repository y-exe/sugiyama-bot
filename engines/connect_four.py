# engines/connect_four.py
import random
from core.constants import ROWS, COLS, CF_EMPTY, CF_P1_TOKEN, CF_P2_TOKEN, CONNECTFOUR_MARKERS

class ConnectFourEngine:
    _next_game_id_counter = 1

    def __init__(self, p1_id, p2_id):
        self.board = [[CF_EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        player_ids = [p1_id, p2_id]
        random.shuffle(player_ids)
        self.players = {CF_P1_TOKEN: player_ids[0], CF_P2_TOKEN: player_ids[1]}
        self.current_player_token = CF_P1_TOKEN
        self.winner = None
        self.game_over = False
        self.message_id = None
        self.channel_id = None
        self.afk_task = None
        self.game_id = ConnectFourEngine._assign_game_id_static()

    @staticmethod
    def _assign_game_id_static():
        gid = ConnectFourEngine._next_game_id_counter
        ConnectFourEngine._next_game_id_counter += 1
        return gid

    def get_current_player_id(self):
        return self.players.get(self.current_player_token)

    def drop_token(self, col):
        if not (0 <= col < COLS) or self.board[0][col] != CF_EMPTY:
            return False
        for r in range(ROWS - 1, -1, -1):
            if self.board[r][col] == CF_EMPTY:
                self.board[r][col] = self.current_player_token
                return True
        return False

    def check_win(self):
        token = self.current_player_token
        if token == CF_EMPTY: return False
        # 横方向
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(self.board[r][c+i] == token for i in range(4)):
                    self.winner = token
                    self.game_over = True
                    return True
        # 縦方向
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(self.board[r+i][c] == token for i in range(4)):
                    self.winner = token
                    self.game_over = True
                    return True
        # 斜め (右下)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(self.board[r+i][c+i] == token for i in range(4)):
                    self.winner = token
                    self.game_over = True
                    return True
        # 斜め (左下)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(self.board[r-i][c+i] == token for i in range(4)):
                    self.winner = token
                    self.game_over = True
                    return True
        return False

    def is_board_full(self):
        full = all(self.board[0][c] != CF_EMPTY for c in range(COLS))
        if full: self.game_over = True
        return full

    def switch_player(self):
        self.current_player_token = CF_P2_TOKEN if self.current_player_token == CF_P1_TOKEN else CF_P1_TOKEN

    def get_bot_move(self) -> int:
        valid_cols = [c for c in range(COLS) if self.board[0][c] == CF_EMPTY]
        if not valid_cols: return -1
        
        my_token = self.current_player_token
        op_token = CF_P1_TOKEN if my_token == CF_P2_TOKEN else CF_P2_TOKEN

        def find_winning_move(token):
            for col in valid_cols:
                # 仮想盤面でシミュレーション
                temp_board = [row[:] for row in self.board]
                placed = False
                for r in range(ROWS - 1, -1, -1):
                    if temp_board[r][col] == CF_EMPTY:
                        temp_board[r][col] = token
                        placed = True
                        break
                if placed:
                    if self._check_win_static(temp_board, token):
                        return col
            return None

        # 1. 自分が勝てる手があるか
        move = find_winning_move(my_token)
        if move is not None: return move
        
        # 2. 相手が次勝つ手を阻止するか
        move = find_winning_move(op_token)
        if move is not None: return move
        
        # 3. 中央優先の戦略
        preferred_order = [3, 4, 2, 5, 1, 6, 0]
        for col in preferred_order:
            if col in valid_cols: return col
            
        return random.choice(valid_cols)

    @staticmethod
    def _check_win_static(board, token):
        # 勝利判定の静的版 (シミュレーション用)
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(board[r][c+i] == token for i in range(4)): return True
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(board[r+i][c] == token for i in range(4)): return True
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(board[r+i][c+i] == token for i in range(4)): return True
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(board[r-i][c+i] == token for i in range(4)): return True
        return False

# スタンドアロン関数としてエクスポート (cogs/games.py からの呼び出し用)
def get_connectfour_bot_move(game: ConnectFourEngine) -> int:
    return game.get_bot_move()