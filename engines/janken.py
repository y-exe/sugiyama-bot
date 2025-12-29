# engines/janken.py
def judge_janken(h1, h2):
    """
    h1, h2: 'rock', 'scissors', 'paper'
    戻り値: 1(h1勝), 2(h2勝), 0(引分)
    """
    if h1 == h2: return 0
    wins = [('rock', 'scissors'), ('scissors', 'paper'), ('paper', 'rock')]
    return 1 if (h1, h2) in wins else 2