import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),
    (50, 200, 50),
    (50, 100, 240),
    (240, 200, 40),
    (180, 50, 220),
    (240, 130, 40),
]

class Gem:
    def __init__(self, color, target_row, col):
        self.color = color
        self.target_row = target_row
        self.col = col
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y

class Board:
    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.reset()

    def reset(self):
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = Gem(random.choice(GEM_COLORS), r, c)
                gem.current_y = gem.target_y
                self.grid[r][c] = gem
        self.resolve_matches()

    def is_animating(self):
        return any(
            self.grid[r][c] and self.grid[r][c].is_animating()
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
        )

    def swap_gems(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        for r, c in (pos1, pos2):
            gem = self.grid[r][c]
            if gem:
                gem.target_row = r
                gem.target_y = r * TILE_SIZE
                gem.current_y = r * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_matches(self):
        matched = set()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 2):
                cells = [(r, c), (r, c + 1), (r, c + 2)]
                gems = [self.grid[rr][cc] for rr, cc in cells]
                if all(gems) and len({gem.color for gem in gems}) == 1:
                    matched.update(cells)
        for r in range(GRID_SIZE - 2):
            for c in range(GRID_SIZE):
                cells = [(r, c), (r + 1, c), (r + 2, c)]
                gems = [self.grid[rr][cc] for rr, cc in cells]
                if all(gems) and len({gem.color for gem in gems}) == 1:
                    matched.update(cells)
        return matched

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None
            for r in range(empty_slots):
                gem = Gem(random.choice(GEM_COLORS), r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem

    def resolve_matches(self):
        total_cleared = 0
        while True:
            matches = self.find_matches()
            if not matches:
                break
            total_cleared += len(matches)
            for r, c in matches:
                self.grid[r][c] = None
            self.drop_and_refill()
        return total_cleared

    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False
        self.swap_gems(pos1, pos2)
        matches = self.find_matches()
        if not matches:
            self.swap_gems(pos1, pos2)
            return False
        self.moves_remaining -= 1
        cleared = self.resolve_matches()
        self.score += cleared * 10
        return True

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

    def render(self, surface):
        board_rect = pygame.Rect(self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE)
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(surface, (255, 255, 255), tile_rect, width=1, border_radius=10)
                if self.selected == (r, c):
                    sel_rect = pygame.Rect(
                        self.offset_x + c * TILE_SIZE + 2,
                        self.offset_y + r * TILE_SIZE + 2,
                        TILE_SIZE - 4,
                        TILE_SIZE - 4,
                    )
                    pygame.draw.rect(surface, (255, 255, 255), sel_rect, width=4, border_radius=10)
