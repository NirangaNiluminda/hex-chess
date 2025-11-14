import math
import pygame
from typing import Tuple
from constants import *

def draw_hexagon(surface: pygame.Surface, center: Tuple[float, float],
                 radius: float, color: Tuple[int, int, int],
                 outline_color: Tuple[int, int, int], highlight: bool = False):
    """Draw a single hexagon with outline."""
    corners = []
    for i in range(6):
        angle_deg = 60 * i
        angle_rad = math.pi / 180 * angle_deg
        x = center[0] + radius * math.cos(angle_rad)
        y = center[1] + radius * math.sin(angle_rad)
        corners.append((x, y))

    # Draw filled hexagon
    pygame.draw.polygon(surface, color, corners)

    # Draw highlight if selected
    if highlight:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        s_corners = [(c[0] - center[0] + radius, c[1] - center[1] + radius) for c in corners]
        pygame.draw.polygon(s, HIGHLIGHT, s_corners)
        surface.blit(s, (center[0] - radius, center[1] - radius))

    # Draw outline
    outline_width = 3 if highlight else 2
    pygame.draw.polygon(surface, outline_color, corners, outline_width)


class Renderer:
    """Render board, pieces and UI. Keeps main loop smaller and focused on events/state."""

    def __init__(self, board, piece_manager, font, small_font, turn_font, window_w, window_h):
        self.board = board
        self.piece_manager = piece_manager
        self.font = font
        self.small_font = small_font
        self.turn_font = turn_font
        self.window_w = window_w
        self.window_h = window_h

    def render(self, screen, center_x, center_y, mouse_pos, hovered_coord,
               selected_tile, dragging, drag_piece, legal_moves,
               reset_button_rect, undo_button_rect, reset_hover, undo_hover, history):
        # Clear screen
        screen.fill(BACKGROUND)

        # Draw all hexagons and pieces
        for (q, r), tile in self.board.tiles.items():
            x, y = self.board.axial_to_pixel(q, r, center_x, center_y)
            tile.pixel_pos = (x, y)

            # Highlight if selected or hovered
            highlight = (q, r) == selected_tile or (q, r) == hovered_coord
            is_legal_move = (q, r) in legal_moves

            draw_hexagon(screen, (x, y), self.board.radius, tile.color, OUTLINE, highlight)

            # Draw legal move indicator
            if is_legal_move:
                corners = []
                for i in range(6):
                    angle_deg = 60 * i
                    angle_rad = math.pi / 180 * angle_deg
                    cx = x + self.board.radius * math.cos(angle_rad)
                    cy = y + self.board.radius * math.sin(angle_rad)
                    corners.append((cx, cy))

                s = pygame.Surface((self.board.radius * 2, self.board.radius * 2), pygame.SRCALPHA)
                s_corners = [(c[0] - x + self.board.radius, c[1] - y + self.board.radius) for c in corners]
                pygame.draw.polygon(s, LEGAL_MOVE_HIGHLIGHT, s_corners)
                screen.blit(s, (x - self.board.radius, y - self.board.radius))

            # Draw piece if present and not being dragged
            if tile.has_piece() and (not dragging or (q, r) != selected_tile):
                piece_color, piece_name = tile.get_piece()
                piece_image = self.piece_manager.get_image(piece_color, piece_name)
                if piece_image:
                    rect = piece_image.get_rect(center=(x, y))
                    screen.blit(piece_image, rect)

        # Draw dragged piece at mouse position
        if dragging and drag_piece:
            piece_color, piece_name = drag_piece
            piece_image = self.piece_manager.get_image(piece_color, piece_name)
            if piece_image:
                rect = piece_image.get_rect(center=mouse_pos)
                screen.blit(piece_image, rect)

        # Draw current turn indicator (top center)
        turn_text = self.turn_font.render(f"Turn: {self.board.current_turn.upper()}", True, (0, 0, 0))
        turn_bg_rect = turn_text.get_rect(center=(self.window_w // 2, 25))
        turn_bg_rect.inflate_ip(20, 10)

        # Draw background for turn indicator
        turn_color = (240, 240, 240) if self.board.current_turn == "white" else (80, 80, 80)
        text_color = (0, 0, 0) if self.board.current_turn == "white" else (255, 255, 255)
        pygame.draw.rect(screen, turn_color, turn_bg_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), turn_bg_rect, 2, border_radius=5)

        turn_text = self.turn_font.render(f"Turn: {self.board.current_turn.upper()}", True, text_color)
        turn_text_rect = turn_text.get_rect(center=(self.window_w // 2, 25))
        screen.blit(turn_text, turn_text_rect)

        # Draw info text
        text = self.font.render(f"Hexagonal Chess - Gliński's Variant", True, (0, 0, 0))
        screen.blit(text, (10, 10))

        info_text = self.small_font.render("Click and drag pieces to move", True, (0, 0, 0))
        screen.blit(info_text, (10, 35))

        if hovered_coord:
            coord_text = self.small_font.render(f"Hex: ({hovered_coord[0]}, {hovered_coord[1]})", True, (0, 0, 0))
            screen.blit(coord_text, (10, 55))

        # Draw reset button
        button_color = (100, 200, 100) if reset_hover else (70, 170, 70)
        pygame.draw.rect(screen, button_color, reset_button_rect, border_radius=5)
        pygame.draw.rect(screen, (40, 40, 40), reset_button_rect, 2, border_radius=5)
        reset_text = self.small_font.render("RESET", True, (255, 255, 255))
        reset_text_rect = reset_text.get_rect(center=reset_button_rect.center)
        screen.blit(reset_text, reset_text_rect)

        # Draw undo button below reset (disabled when no history)
        undo_enabled = len(history) > 0
        undo_color = (100, 150, 250) if (undo_hover and undo_enabled) else ((80, 130, 220) if undo_enabled else (140, 140, 140))
        pygame.draw.rect(screen, undo_color, undo_button_rect, border_radius=5)
        pygame.draw.rect(screen, (40, 40, 40), undo_button_rect, 2, border_radius=5)
        undo_text = self.small_font.render("UNDO", True, (255, 255, 255) if undo_enabled else (200, 200, 200))
        undo_text_rect = undo_text.get_rect(center=undo_button_rect.center)
        screen.blit(undo_text, undo_text_rect)

        # Get and display game status
        game_status = self.board.get_game_status()
        status_y = self.window_h - 40

        if game_status == 'check':
            status_text = self.turn_font.render("CHECK!", True, (200, 0, 0))
            status_rect = status_text.get_rect(center=(self.window_w // 2, status_y))
            # Draw background
            bg_rect = status_rect.inflate(20, 10)
            pygame.draw.rect(screen, (255, 255, 200), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (200, 0, 0), bg_rect, 2, border_radius=5)
            screen.blit(status_text, status_rect)
        elif game_status == 'checkmate':
            winner = "BLACK" if self.board.current_turn == "white" else "WHITE"
            status_text = self.turn_font.render(f"CHECKMATE! {winner} WINS!", True, (200, 0, 0))
            status_rect = status_text.get_rect(center=(self.window_w // 2, status_y))
            # Draw background
            bg_rect = status_rect.inflate(20, 10)
            pygame.draw.rect(screen, (255, 200, 200), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (200, 0, 0), bg_rect, 3, border_radius=5)
            screen.blit(status_text, status_rect)
        elif game_status == 'stalemate':
            status_text = self.turn_font.render("STALEMATE! DRAW!", True, (100, 100, 100))
            status_rect = status_text.get_rect(center=(self.window_w // 2, status_y))
            # Draw background
            bg_rect = status_rect.inflate(20, 10)
            pygame.draw.rect(screen, (220, 220, 220), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), bg_rect, 3, border_radius=5)
            screen.blit(status_text, status_rect)

        pygame.display.flip()