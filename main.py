import pygame
import math
from typing import Tuple
from constants import *
from hex_board import HexBoard
from asset_manager import PieceImageManager

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


def setup_initial_board(board: HexBoard):
    """Set up the initial chess piece positions."""
    # Clear the board first
    for tile in board.tiles.values():
        tile.remove_piece()
    
    # WHITE pieces
    board.place_piece(1, 4, "white", "king")
    board.place_piece(-1, 5, "white", "queen")
    board.place_piece(3, 2, "white", "rook")
    board.place_piece(-3, 5, "white", "rook")
    board.place_piece(2, 3, "white", "knight")
    board.place_piece(-2, 5, "white", "knight")
    board.place_piece(0, 5, "white", "bishop")
    board.place_piece(0, 4, "white", "bishop")
    board.place_piece(0, 3, "white", "bishop")
    board.place_piece(-4, 5, "white", "pawn")
    board.place_piece(-3, 4, "white", "pawn")
    board.place_piece(-2, 3, "white", "pawn")
    board.place_piece(-1, 2, "white", "pawn")
    board.place_piece(0, 1, "white", "pawn")
    board.place_piece(1, 1, "white", "pawn")
    board.place_piece(2, 1, "white", "pawn")
    board.place_piece(3, 1, "white", "pawn")
    board.place_piece(4, 1, "white", "pawn")
    
    # BLACK pieces
    board.place_piece(1, -5, "black", "king")
    board.place_piece(-1, -4, "black", "queen")
    board.place_piece(3, -5, "black", "rook")
    board.place_piece(-3, -2, "black", "rook")
    board.place_piece(2, -5, "black", "knight")
    board.place_piece(-2, -3, "black", "knight")
    board.place_piece(0, -5, "black", "bishop")
    board.place_piece(0, -4, "black", "bishop")
    board.place_piece(0, -3, "black", "bishop")
    board.place_piece(4, -5, "black", "pawn")
    board.place_piece(3, -4, "black", "pawn")
    board.place_piece(2, -3, "black", "pawn")
    board.place_piece(1, -2, "black", "pawn")
    board.place_piece(0, -1, "black", "pawn")
    board.place_piece(-1, -1, "black", "pawn")
    board.place_piece(-2, -1, "black", "pawn")
    board.place_piece(-3, -1, "black", "pawn")
    board.place_piece(-4, -1, "black", "pawn")


def main():
    """Main game loop."""
    pygame.init()
    # Try to adapt the board size to the current display so it fits smaller screens.
    info = pygame.display.Info()
    margin = 80
    avail_w = max(300, info.current_w - margin) if info.current_w else WINDOW_WIDTH
    avail_h = max(300, info.current_h - margin) if info.current_h else WINDOW_HEIGHT

    # Create a temporary board with the default radius to compute how many pixels it needs
    temp_board = HexBoard(BOARD_SIZE, HEX_RADIUS)
    xs, ys = [], []
    for (q, r) in temp_board.tiles.keys():
        x, y = temp_board.axial_to_pixel(q, r, 0, 0)
        xs.append(x)
        ys.append(y)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    needed_w = (max_x - min_x) + 2 * temp_board.radius
    needed_h = (max_y - min_y) + 2 * temp_board.radius

    # Determine scale factor to fit the available window
    scale = min(avail_w / needed_w, avail_h / needed_h, 1.0)
    scaled_radius = max(8, int(HEX_RADIUS * scale))

    # Final window size: keep configured window but don't exceed available display
    window_w = int(min(WINDOW_WIDTH, avail_w))
    window_h = int(min(WINDOW_HEIGHT, avail_h))
    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption("Hexagonal Chess Board")
    clock = pygame.time.Clock()
    
    # Create the hex board and piece manager using the scaled radius
    board = HexBoard(BOARD_SIZE, scaled_radius)
    piece_manager = PieceImageManager(hex_radius=scaled_radius)
    
    # Set up initial piece positions
    setup_initial_board(board)
    
    # Calculate center of screen using the actual window size
    center_x = window_w // 2
    center_y = window_h // 2
    
    # Reset button setup
    button_width = 100
    button_height = 40
    button_x = window_w - button_width - 10
    button_y = 10
    reset_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    
    # For piece dragging
    selected_tile = None
    dragging = False
    drag_piece = None
    legal_moves = []  # Store legal moves for selected piece
    
    # Font for info
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        hovered_coord = board.pixel_to_axial(mouse_pos[0], mouse_pos[1], center_x, center_y)
        button_hovered = reset_button_rect.collidepoint(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:  # R key also resets
                    setup_initial_board(board)
                    selected_tile = None
                    dragging = False
                    drag_piece = None
                    legal_moves = []
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if reset button was clicked
                if button_hovered:
                    setup_initial_board(board)
                    selected_tile = None
                    dragging = False
                    drag_piece = None
                    legal_moves = []
                elif hovered_coord:
                    tile = board.get_tile(*hovered_coord)
                    if tile and tile.has_piece():
                        selected_tile = hovered_coord
                        dragging = True
                        drag_piece = tile.get_piece()
                        # Calculate legal moves for this piece
                        legal_moves = board.get_legal_moves(*hovered_coord)
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging and selected_tile and hovered_coord:
                    # Only move if destination is a legal move
                    if hovered_coord in legal_moves:
                        board.move_piece(selected_tile[0], selected_tile[1], 
                                       hovered_coord[0], hovered_coord[1])
                dragging = False
                selected_tile = None
                drag_piece = None
                legal_moves = []  # Clear legal moves
        
        # Clear screen
        screen.fill(BACKGROUND)
        
        # Draw all hexagons and pieces
        for (q, r), tile in board.tiles.items():
            x, y = board.axial_to_pixel(q, r, center_x, center_y)
            tile.pixel_pos = (x, y)
            
            # Highlight if selected or hovered
            highlight = (q, r) == selected_tile or (q, r) == hovered_coord
            is_legal_move = (q, r) in legal_moves
            
            draw_hexagon(screen, (x, y), board.radius, tile.color, OUTLINE, highlight)
            
            # Draw legal move indicator
            if is_legal_move:
                corners = []
                for i in range(6):
                    angle_deg = 60 * i
                    angle_rad = math.pi / 180 * angle_deg
                    cx = x + board.radius * math.cos(angle_rad)
                    cy = y + board.radius * math.sin(angle_rad)
                    corners.append((cx, cy))
                
                s = pygame.Surface((board.radius * 2, board.radius * 2), pygame.SRCALPHA)
                s_corners = [(c[0] - x + board.radius, c[1] - y + board.radius) for c in corners]
                pygame.draw.polygon(s, LEGAL_MOVE_HIGHLIGHT, s_corners)
                screen.blit(s, (x - board.radius, y - board.radius))
            
            # Draw piece if present and not being dragged
            if tile.has_piece() and (not dragging or (q, r) != selected_tile):
                piece_color, piece_name = tile.get_piece()
                piece_image = piece_manager.get_image(piece_color, piece_name)
                if piece_image:
                    rect = piece_image.get_rect(center=(x, y))
                    screen.blit(piece_image, rect)
        
        # Draw dragged piece at mouse position
        if dragging and drag_piece:
            piece_color, piece_name = drag_piece
            piece_image = piece_manager.get_image(piece_color, piece_name)
            if piece_image:
                rect = piece_image.get_rect(center=mouse_pos)
                screen.blit(piece_image, rect)
        
        # Draw info text
        text = font.render(f"Hexagonal Board: {BOARD_SIZE} per side", True, (0, 0, 0))
        screen.blit(text, (10, 10))
        
        info_text = small_font.render("Click and drag pieces to move them", True, (0, 0, 0))
        screen.blit(info_text, (10, 35))
        
        if hovered_coord:
            coord_text = small_font.render(f"Hex: ({hovered_coord[0]}, {hovered_coord[1]})", True, (0, 0, 0))
            screen.blit(coord_text, (10, 55))
        
        # Draw reset button
        button_color = (100, 200, 100) if button_hovered else (70, 170, 70)
        pygame.draw.rect(screen, button_color, reset_button_rect, border_radius=5)
        pygame.draw.rect(screen, (40, 40, 40), reset_button_rect, 2, border_radius=5)
        
        reset_text = small_font.render("RESET", True, (255, 255, 255))
        reset_text_rect = reset_text.get_rect(center=reset_button_rect.center)
        screen.blit(reset_text, reset_text_rect)
        
        # Show keyboard shortcut hint
        hint_text = small_font.render("Press R to reset", True, (100, 100, 100))
        screen.blit(hint_text, (window_w - 120, button_y + button_height + 5))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()