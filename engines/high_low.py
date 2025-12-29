# engines/high_low.py
import random

class HighLowLogic:
    def __init__(self, host_id, opponent_id, bet_amount, message_id):
        self.players = [host_id, opponent_id]
        self.bet = bet_amount
        self.choices = {host_id: None, opponent_id: None}
        self.current_card = random.randint(1, 13)
        self.message_id = message_id

    def get_card_display(self, card_value=None):
        target = card_value if card_value is not None else self.current_card
        mapping = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return mapping.get(target, str(target))