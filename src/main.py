import pygame
import copy
from constants import *
from hex_board import HexBoard
from asset_manager import PieceImageManager
from renderer import Renderer
from game import MoveValidator

def setup_initial_board(board: HexBoard):
    """Set up the initial chess piece positions."""
    # Clear the board first
    for tile in board.tiles.values():
        tile.remove_piece()
    
    # Reset turn to white
    board.current_turn = "white"
    board.en_passant_target = None
    board.pending_promotion = None
    
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

    promotion_pieces = ["queen", "rook", "bishop", "knight"]
    promotion_button_size = 60
    promotion_buttons = {}

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
    undo_button_rect = pygame.Rect(button_x, button_y + button_height + 10, button_width, button_height)
    flip_button_rect = pygame.Rect(button_x, button_y + (button_height + 10) * 2, button_width, button_height)

    # For piece dragging
    selected_tile = None
    dragging = False
    drag_piece = None
    legal_moves = []  # Store legal moves for selected piece
    history = [] # store previous board states (deep copies)
     
    # Font for info
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)
    turn_font = pygame.font.Font(None, 32)

    renderer = Renderer(board, piece_manager, font, small_font, turn_font, window_w, window_h)
    move_validator = MoveValidator(board)
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        hovered_coord = board.pixel_to_axial(mouse_pos[0], mouse_pos[1], center_x, center_y)
        # If the board is  flipped, the pixel mapping is reversed
        # so convert the hovered coordinate back into board/data coordinates.
        if hovered_coord and getattr(board, 'flipped', False):
            hovered_coord = (-hovered_coord[0], -hovered_coord[1])

        reset_hover = reset_button_rect.collidepoint(mouse_pos)
        undo_hover = undo_button_rect.collidepoint(mouse_pos)
        flip_hover = flip_button_rect.collidepoint(mouse_pos)

        # Check promotion button hover
        promotion_hover = None
        if board.pending_promotion:
            for piece, rect in promotion_buttons.items():
                if rect.collidepoint(mouse_pos):
                    promotion_hover = piece
                    break
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle promotion choice first
                if board.pending_promotion and promotion_hover:
                    board.promote_pawn(promotion_hover)
                    promotion_buttons = {}
                    continue
                # check if reset button was clicked
                if reset_hover:
                    setup_initial_board(board)
                    # Ensure renderer and move validator reference the same board
                    renderer.board = board
                    move_validator.board = board
                    move_validator.move_generator.board = board
                    selected_tile = None
                    dragging = False
                    drag_piece = None
                    legal_moves = []
                    history = []
                elif undo_hover:
                    if history:
                        board = history.pop()
                        renderer.board = board
                        # Ensure renderer and move validator reference the same board
                        renderer.board = board
                        move_validator.board = board
                        move_validator.move_generator.board = board
                        selected_tile = None
                        dragging = False
                        drag_piece = None
                        legal_moves = []
                elif flip_hover:
                    board.toggle_flip()
                elif hovered_coord:
                    tile = board.get_tile(*hovered_coord)
                    if tile and tile.has_piece():
                        piece_color, _ = tile.get_piece()
                        # Only allow selecting pieces of the current turn
                        if piece_color == board.current_turn:
                            selected_tile = hovered_coord
                            dragging = True
                            drag_piece = tile.get_piece()
                            # Calculate legal moves for this piece (check-aware)
                            legal_moves = move_validator.get_legal_moves_with_check(*hovered_coord)
            elif event.type == pygame.MOUSEBUTTONUP:
                move_made = False
                if dragging and selected_tile and hovered_coord:
                    # Only move if destination is a legal move
                    if hovered_coord in legal_moves:
                        history.append(copy.deepcopy(board))
                        move_made = board.move_piece(selected_tile[0], selected_tile[1], 
                                       hovered_coord[0], hovered_coord[1])
                
                # Always clear selection after mouse release
                dragging = False
                selected_tile = None
                drag_piece = None
                legal_moves = []  # Clear legal moves
        
        # Clear screen
        screen.fill(BACKGROUND)
        
        # Calculate promotion button positions if needed
        if board.pending_promotion:
            q, r, color = board.pending_promotion
            total_width = len(promotion_pieces) * (promotion_button_size + 10) - 10
            start_x = (window_w - total_width) // 2
            start_y = window_h // 2 - promotion_button_size // 2
            
            promotion_buttons = {}
            for i, piece in enumerate(promotion_pieces):
                x = start_x + i * (promotion_button_size + 10)
                promotion_buttons[piece] = pygame.Rect(x, start_y, 
                                                       promotion_button_size, 
                                                       promotion_button_size)
                
        # Draw all hexagons and pieces
        renderer.render(screen, center_x, center_y, mouse_pos, hovered_coord,
                selected_tile, dragging, drag_piece, legal_moves,
                reset_button_rect, undo_button_rect, flip_button_rect,
                reset_hover, undo_hover, flip_hover, history,promotion_buttons, promotion_hover)
        
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()