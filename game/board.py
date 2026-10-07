import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50), (50, 200, 50), (50, 100, 240),
    (240, 200, 40), (180, 50, 220), (240, 130, 40),
]

class Gem:
    def __init__(self, color, target_row, col, special=None):
        self.color = color
        self.target_row = target_row
        self.col = col
        self.special = special
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
        self.offset_x, self.offset_y = offset_x, offset_y
        self.target_score, self.max_moves = target_score, max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.cascade = 1
        self.last_cascade = 0
        self.reset()

    def reset(self):
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        self.cascade = 1
        self.last_cascade = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = Gem(random.choice(GEM_COLORS), r, c)
                gem.current_y = gem.target_y
                self.grid[r][c] = gem
        self.resolve_matches()

    def is_animating(self):
        return any(self.grid[r][c] and self.grid[r][c].is_animating()
                   for r in range(GRID_SIZE) for c in range(GRID_SIZE))

    def swap_gems(self, pos1, pos2):
        r1, c1 = pos1; r2, c2 = pos2
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        for r, c in (pos1, pos2):
            gem = self.grid[r][c]
            if gem:
                gem.target_row = r
                gem.target_y = r * TILE_SIZE
                gem.current_y = r * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1; r2, c2 = pos2
        return abs(r1-r2) + abs(c1-c2) == 1

    def find_matches(self):
        matched = set()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE-2):
                cells = [(r,c),(r,c+1),(r,c+2)]
                gems = [self.grid[rr][cc] for rr,cc in cells]
                if all(gems) and len({g.color for g in gems}) == 1:
                    matched.update(cells)
        for r in range(GRID_SIZE-2):
            for c in range(GRID_SIZE):
                cells = [(r,c),(r+1,c),(r+2,c)]
                gems = [self.grid[rr][cc] for rr,cc in cells]
                if all(gems) and len({g.color for g in gems}) == 1:
                    matched.update(cells)
        return matched

    def find_four_matches(self):
        lines = []
        for r in range(GRID_SIZE):
            c = 0
            while c < GRID_SIZE:
                if not self.grid[r][c]:
                    c += 1; continue
                color = self.grid[r][c].color
                start = c
                while c < GRID_SIZE and self.grid[r][c] and self.grid[r][c].color == color:
                    c += 1
                if c-start >= 4:
                    lines.append(("row", r, list(range(start,c))))
        for c in range(GRID_SIZE):
            r = 0
            while r < GRID_SIZE:
                if not self.grid[r][c]:
                    r += 1; continue
                color = self.grid[r][c].color
                start = r
                while r < GRID_SIZE and self.grid[r][c] and self.grid[r][c].color == color:
                    r += 1
                if r-start >= 4:
                    lines.append(("col", c, list(range(start,r))))
        return lines

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE-1,-1,-1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r+empty_slots][c] = gem
                    self.grid[r][c] = None
            for r in range(empty_slots):
                gem = Gem(random.choice(GEM_COLORS), r, c)
                gem.current_y = -((empty_slots-r) * TILE_SIZE)
                self.grid[r][c] = gem

    def resolve_matches(self):
        total = 0
        chain = 1
        while True:
            matches = self.find_matches()
            if not matches:
                break
            total += len(matches)
            self.score += len(matches) * 10 * chain
            self.last_cascade = chain
            chain += 1
            for r,c in matches:
                self.grid[r][c] = None
            self.drop_and_refill()
        return total

    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1,pos2) or self.is_game_over() or self.is_animating():
            return False
        self.swap_gems(pos1,pos2)
        matches = self.find_matches()
        if not matches:
            self.swap_gems(pos1,pos2)
            return False
        self.moves_remaining -= 1
        self.cascade = 1
        self.last_cascade = 1
        # Four-match special: replace the first matched gem on the matching line.
        four_lines = self.find_four_matches()
        consumed_special = None
        for orientation, fixed, cells in four_lines:
            candidate = (fixed, cells[0]) if orientation == "row" else (cells[0], fixed)
            if candidate in matches:
                consumed_special = candidate
                break
        if consumed_special:
            r,c = consumed_special
            color = self.grid[r][c].color
            self.grid[r][c] = Gem(color, r, c, special="row" if four_lines[0][0]=="row" else "col")
            matches.remove((r,c))
        self.resolve_selected_matches(matches)
        return True

    def resolve_selected_matches(self, matches):
        self.score += len(matches) * 10
        for r,c in list(matches):
            gem = self.grid[r][c]
            if gem and gem.special:
                if gem.special == "row":
                    for cc in range(GRID_SIZE):
                        if self.grid[r][cc] is not None:
                            self.grid[r][cc] = None
                else:
                    for rr in range(GRID_SIZE):
                        if self.grid[rr][c] is not None:
                            self.grid[rr][c] = None
            else:
                self.grid[r][c] = None
        self.drop_and_refill()
        while True:
            nxt = self.find_matches()
            if not nxt:
                break
            self.score += len(nxt) * 10
            for r,c in nxt:
                self.grid[r][c] = None
            self.drop_and_refill()

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score: return "WIN"
        if self.moves_remaining <= 0: return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]: self.grid[r][c].update()

    def would_match_after_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2):
            return False
        self.grid[pos1[0]][pos1[1]], self.grid[pos2[0]][pos2[1]] = self.grid[pos2[0]][pos2[1]], self.grid[pos1[0]][pos1[1]]
        has_match = bool(self.find_matches())
        self.grid[pos1[0]][pos1[1]], self.grid[pos2[0]][pos2[1]] = self.grid[pos2[0]][pos2[1]], self.grid[pos1[0]][pos1[1]]
        return has_match

    def render(self, surface, hint_pair=None, hint_phase=0.0):
        board_rect = pygame.Rect(self.offset_x,self.offset_y,GRID_SIZE*TILE_SIZE,GRID_SIZE*TILE_SIZE)
        pygame.draw.rect(surface,(20,22,28),board_rect,border_radius=8)
        pygame.draw.rect(surface,(60,65,75),board_rect,width=3,border_radius=8)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    tile = pygame.Rect(self.offset_x+c*TILE_SIZE+2,self.offset_y+gem.current_y+2,TILE_SIZE-4,TILE_SIZE-4)
                    pygame.draw.rect(surface,gem.color,tile,border_radius=10)
                    pygame.draw.rect(surface,(255,255,255),tile,width=1,border_radius=10)
                    if gem.special:
                        pygame.draw.rect(surface,(255,255,255),tile.inflate(-10,-10),width=3,border_radius=8)
                        pygame.draw.circle(surface,(255,255,255),tile.center,7,2)
                if hint_pair and (r,c) in hint_pair:
                    pulse = int(2 + 3 * (0.5 + 0.5 * __import__("math").sin(hint_phase)))
                    hint_rect = pygame.Rect(
                        self.offset_x + c*TILE_SIZE + 4,
                        self.offset_y + r*TILE_SIZE + 4,
                        TILE_SIZE - 8,
                        TILE_SIZE - 8,
                    )
                    pygame.draw.rect(surface, (255, 255, 255), hint_rect, width=pulse + 1, border_radius=12)
                if self.selected == (r,c):
                    sel=pygame.Rect(self.offset_x+c*TILE_SIZE+2,self.offset_y+r*TILE_SIZE+2,TILE_SIZE-4,TILE_SIZE-4)
                    pygame.draw.rect(surface,(255,255,255),sel,width=4,border_radius=10)
