import math
import time
import pygame
from typing import Tuple
from constants import *
from game import MoveValidator
from evaluation import Evaluator

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

    def _draw_captured_pieces(self, screen, center_x, center_y):
        """Draw captured pieces - Green box (left) = your captures, Red box (right) = your losses."""

        # ---- UI constants ----
        piece_size = max(26, int(self.board.radius * 0.8))
        h_space = piece_size + 4
        v_space = piece_size + 4
        pieces_per_row = 2

        header_h = 22
        section_pad = 6
        bottom_pad = 6
        side_pad = 8

        available_top = 250
        available_h = self.window_h - available_top - 70

        # ---- Get captured pieces ----
        white_captured = self.board.captured_pieces.get("white", [])
        black_captured = self.board.captured_pieces.get("black", [])

        if getattr(self.board, "flipped", False):
            # Viewing from black side
            green_pieces, green_color = white_captured, "white"
            red_pieces, red_color = black_captured, "black"
        else:
            # Viewing from white side
            green_pieces, green_color = black_captured, "black"
            red_pieces, red_color = white_captured, "white"

        # ---- Shared panel rendering function ----
        def draw_panel(pieces, piece_color, panel_x, label, border_color, text_color):
            if not pieces:
                return

            # Determine needed rows
            rows = (len(pieces) + pieces_per_row - 1) // pieces_per_row
            panel_h = header_h + section_pad + (rows * v_space) + bottom_pad

            # Handle vertical overflow
            if panel_h > available_h:
                max_rows = max(1, (available_h - header_h - section_pad - bottom_pad) // v_space)
                rows = max_rows
                panel_h = header_h + section_pad + (rows * v_space) + bottom_pad
                max_pieces = rows * pieces_per_row
                display = pieces[-max_pieces:]
                overflow = len(pieces) > max_pieces
            else:
                display = pieces
                overflow = False

            # Panel position
            panel_y = available_top
            panel_w = pieces_per_row * h_space + side_pad * 2 + 10
            panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

            # Background + border
            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (245, 245, 245, 230), panel_surf.get_rect(), border_radius=6)
            screen.blit(panel_surf, panel_rect)
            pygame.draw.rect(screen, border_color, panel_rect, 3, border_radius=6)

            # Header label
            text = self.small_font.render(label, True, text_color)
            text_rect = text.get_rect(center=(panel_x + panel_w // 2, panel_y + header_h // 2))
            screen.blit(text, text_rect)

            # Draw piece icons in grid
            start_y = panel_y + header_h + section_pad
            for i, piece_name in enumerate(display):
                row, col = divmod(i, pieces_per_row)
                x = panel_x + side_pad + col * h_space + h_space // 2
                y = start_y + row * v_space + v_space // 2

                img = self.piece_manager.get_image(piece_color, piece_name)
                if img:
                    scaled = pygame.transform.smoothscale(img, (piece_size, piece_size))
                    screen.blit(scaled, scaled.get_rect(center=(x, y)))

            # Overflow indicator
            if overflow:
                extra = len(pieces) - len(display)
                overflow_txt = self.small_font.render(f"↑ +{extra}", True, text_color)
                overflow_rect = overflow_txt.get_rect(center=(panel_x + panel_w // 2, start_y + 8))
                bg = overflow_rect.inflate(8, 4)
                pygame.draw.rect(screen, (255, 255, 255, 200), bg, border_radius=3)
                screen.blit(overflow_txt, overflow_rect)

        # ---- Draw Left + Right Panels ----
        panel_w = pieces_per_row * h_space + side_pad * 2 + 10

        draw_panel(
            green_pieces,
            green_color,
            panel_x=50,
            label="Captured",
            border_color=(50, 200, 50),
            text_color=(40, 120, 40),
        )

        draw_panel(
            red_pieces,
            red_color,
            panel_x=self.window_w - panel_w - 30,
            label="Lost",
            border_color=(200, 50, 50),
            text_color=(150, 40, 40),
        )

    def render(self, screen, center_x, center_y, mouse_pos, hovered_coord,
               selected_tile, dragging, drag_piece, legal_moves,
               reset_button_rect, undo_button_rect, flip_button_rect,
               reset_hover, undo_hover, flip_hover, history,
               promotion_buttons=None, promotion_hover=None, flip_locked=False,
               last_move=None, engine_thinking=False):
        # Clear screen
        screen.fill(BACKGROUND)

        # Draw all hexagons and pieces
        for (q, r), tile in self.board.tiles.items():
            # If the board is flipped, render tile (q,r) at the pixel
            # position of (-q,-r) so the visual orientation is rotated 180°.
            if getattr(self.board, 'flipped', False):
                display_q, display_r = -q, -r
            else:
                display_q, display_r = q, r

            x, y = self.board.axial_to_pixel(display_q, display_r, center_x, center_y)
            tile.pixel_pos = (x, y)

            # Check if this tile is part of the last move
            is_last_move_start = last_move and (q, r) == (last_move[0], last_move[1])
            is_last_move_end = last_move and (q, r) == (last_move[2], last_move[3])
            
            # Highlight if selected or hovered
            highlight = (q, r) == selected_tile or (q, r) == hovered_coord
            is_legal_move = (q, r) in legal_moves

            draw_hexagon(screen, (x, y), self.board.radius, tile.color, OUTLINE, highlight)

            # Draw last move highlight (orange for start, yellow for end)
            if is_last_move_start or is_last_move_end:
                corners = []
                for i in range(6):
                    angle_deg = 60 * i
                    angle_rad = math.pi / 180 * angle_deg
                    cx = x + self.board.radius * math.cos(angle_rad)
                    cy = y + self.board.radius * math.sin(angle_rad)
                    corners.append((cx, cy))

                s = pygame.Surface((self.board.radius * 2, self.board.radius * 2), pygame.SRCALPHA)
                s_corners = [(c[0] - x + self.board.radius, c[1] - y + self.board.radius) for c in corners]
                
                # Use constants for engine move highlighting
                if is_last_move_start:
                    highlight_color = ENGINE_MOVE_START
                else:
                    highlight_color = ENGINE_MOVE_END
                    
                pygame.draw.polygon(s, highlight_color, s_corners)
                screen.blit(s, (x - self.board.radius, y - self.board.radius))

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
        if engine_thinking:
            turn_text = self.turn_font.render("ENGINE THINKING...", True, (255, 255, 255))
            turn_bg_rect = turn_text.get_rect(center=(self.window_w // 2, 25))
            turn_bg_rect.inflate_ip(20, 10)
            # Pulsing effect for thinking indicator
            pulse = int(abs(math.sin(time.time() * 3) * 30))
            turn_color = (70 + pulse, 130 + pulse, 180 + pulse)
            pygame.draw.rect(screen, turn_color, turn_bg_rect, border_radius=5)
            pygame.draw.rect(screen, (255, 255, 255), turn_bg_rect, 2, border_radius=5)
            screen.blit(turn_text, turn_text.get_rect(center=(self.window_w // 2, 25)))
        else:
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

        # Draw flip button below undo
        if flip_locked:
            # Disabled color
            flip_color = (130, 130, 130)
            text_color = (200, 200, 200)
        else:
            flip_color = (200, 150, 100) if flip_hover else (170, 120, 80)
            text_color = (255, 255, 255)
        
        pygame.draw.rect(screen, flip_color, flip_button_rect, border_radius=5)
        pygame.draw.rect(screen, (40, 40, 40), flip_button_rect, 2, border_radius=5)
        flip_text = self.small_font.render("FLIP", True, text_color)
        flip_text_rect = flip_text.get_rect(center=flip_button_rect.center)
        screen.blit(flip_text, flip_text_rect)

        # Get and display game status
        move_validator = MoveValidator(self.board)
        game_status = move_validator.get_game_status()
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

        # Draw captured pieces before evaluation bar
        self._draw_captured_pieces(screen, center_x, center_y)
        # Draw evaluation bar on the left: white advantage fills upward, black fills downward
        score, total, phase = Evaluator.evaluate(self.board)
        frac = 0.0
        if total and total > 0:
            # fraction in range -1..1
            frac = max(-1.0, min(1.0, score / float(total)))

        bar_width = 20
        bar_x = 10
        bar_y = 60
        bar_height = max(80, self.window_h - 140)
        center_y = bar_y + bar_height / 2
        half = bar_height / 2

        # Bar background and outline
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), border_radius=6)
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=6)

        # Fill depending on advantage
        inner_x = bar_x + 2
        inner_w = bar_width - 4
        if frac > 0:
            fill_h = int(frac * half)
            fill_rect = pygame.Rect(inner_x, int(center_y - fill_h), inner_w, max(1, fill_h))
            pygame.draw.rect(screen, (245, 245, 245), fill_rect, border_radius=4)
        elif frac < 0:
            fill_h = int(-frac * half)
            fill_rect = pygame.Rect(inner_x, int(center_y), inner_w, max(1, fill_h))
            pygame.draw.rect(screen, (30, 30, 30), fill_rect, border_radius=4)

        # Center neutral marker
        pygame.draw.line(screen, (0, 0, 0), (bar_x, center_y), (bar_x + bar_width, center_y), 2)

        # Numeric evaluation display below bar
        eval_text = self.small_font.render(f"{int(score):+d}", True, (0, 0, 0))
        eval_rect = eval_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height + 12))
        screen.blit(eval_text, eval_rect)

         # Draw promotion dialog if needed
        if self.board.pending_promotion and promotion_buttons:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((self.window_w, self.window_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # Draw promotion title
            q, r, color = self.board.pending_promotion
            title_text = self.turn_font.render("Choose Promotion Piece", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(self.window_w // 2, self.window_h // 2 - 80))
            screen.blit(title_text, title_rect)
            
            # Draw promotion buttons
            for piece, rect in promotion_buttons.items():
                # Button background
                button_color = (100, 150, 250) if piece == promotion_hover else (70, 120, 200)
                pygame.draw.rect(screen, button_color, rect, border_radius=5)
                pygame.draw.rect(screen, (255, 255, 255), rect, 3, border_radius=5)
                
                # Draw piece image
                piece_image = self.piece_manager.get_image(color, piece)
                if piece_image:
                    img_rect = piece_image.get_rect(center=rect.center)
                    screen.blit(piece_image, img_rect)
                else:
                    # Fallback text if image not available
                    piece_text = self.small_font.render(piece.upper(), True, (255, 255, 255))
                    text_rect = piece_text.get_rect(center=rect.center)
                    screen.blit(piece_text, text_rect)

        pygame.display.flip()