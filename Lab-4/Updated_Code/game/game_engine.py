import pygame
import time
from game.board import Board, GRID_SIZE, TILE_SIZE

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        offset_x = (width - GRID_SIZE * TILE_SIZE) // 2
        offset_y = (height - GRID_SIZE * TILE_SIZE) // 2 + 30
        self.board = Board(offset_x, offset_y, target_score=500, max_moves=20)
        self.font_big = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 24)
        self.last_input_time = time.monotonic()
        self.hint_pair = None
        self.hint_phase = 0.0

    def mark_input(self):
        self.last_input_time = time.monotonic()
        self.hint_pair = None

    def handle_click(self, mouse_pos):
        self.mark_input()
        if self.board.is_game_over() or self.board.is_animating():
            return
        mx, my = mouse_pos
        bx, by = mx - self.board.offset_x, my - self.board.offset_y
        if 0 <= bx < GRID_SIZE * TILE_SIZE and 0 <= by < GRID_SIZE * TILE_SIZE:
            col, row = int(bx // TILE_SIZE), int(by // TILE_SIZE)
            if self.board.selected is None:
                self.board.selected = (row, col)
            else:
                prev = self.board.selected
                if prev == (row, col):
                    self.board.selected = None
                else:
                    self.board.process_swap(prev, (row, col))
                    self.board.selected = None

    def reset(self):
        self.mark_input()
        self.board.reset()

    def find_hint(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                pos = (r, c)
                for dr, dc in ((0, 1), (1, 0)):
                    other = (r + dr, c + dc)
                    if other[0] >= GRID_SIZE or other[1] >= GRID_SIZE:
                        continue
                    if self.board.would_match_after_swap(pos, other):
                        return (pos, other)
        return None

    def update(self):
        self.board.update()
        now = time.monotonic()
        if not self.board.is_game_over() and not self.board.is_animating():
            if now - self.last_input_time >= 5.0:
                if self.hint_pair is None:
                    self.hint_pair = self.find_hint()
                self.hint_phase = (now - self.last_input_time) * 4.0

    def render(self, screen):
        screen.fill((32, 34, 40))
        title = self.font_big.render("MATCH-3 GEM SWAP", True, (240, 240, 240))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 10))
        combo = f"  |  CASCADE x{self.board.last_cascade}" if self.board.last_cascade > 1 else ""
        hud = f"SCORE: {self.board.score} / {self.board.target_score}   |   MOVES LEFT: {self.board.moves_remaining}{combo}"
        hud_surf = self.font_small.render(hud, True, (80, 220, 180))
        screen.blit(hud_surf, (self.width // 2 - hud_surf.get_width() // 2, 55))
        self.board.render(screen, self.hint_pair, self.hint_phase)

        inst = self.font_small.render("Swap gems to match 3+. Press [R] to Restart.", True, (180, 180, 180))
        screen.blit(inst, (self.width // 2 - inst.get_width() // 2, self.height - 25))

        result = self.board.check_result()
        if result:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))
            msg = "STAGE CLEARED!" if result == "WIN" else "OUT OF MOVES!"
            color = (80, 220, 80) if result == "WIN" else (240, 80, 80)
            res_surf = self.font_big.render(msg, True, color)
            screen.blit(res_surf, (self.width // 2 - res_surf.get_width() // 2, self.height // 2 - 40))
            sub = self.font_small.render(f"Final Score: {self.board.score}  |  Press [R] to Play Again", True, (220, 220, 220))
            screen.blit(sub, (self.width // 2 - sub.get_width() // 2, self.height // 2 + 10))
