# player.py


class Player:
    def __init__(self, player_id: int, name: str, is_human: bool = True):
        """
        player_id : 1 hoặc 2
        name      : tên hiển thị
        is_human  : True = người, False = AI
        """
        self.player_id = player_id
        self.name      = name
        self.is_human  = is_human
        self.score     = 0

    def add_score(self, points: int):
        self.score += points

    def reset_score(self):
        self.score = 0

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "name":      self.name,
            "is_human":  self.is_human,
            "score":     self.score,
        }

    @classmethod
    def from_dict(cls, data):
        p = cls(data["player_id"], data["name"], data["is_human"])
        p.score = data["score"]
        return p

    def __repr__(self):
        kind = "Human" if self.is_human else "AI"
        return f"Player({self.player_id}, {self.name}, {kind}, score={self.score})"
