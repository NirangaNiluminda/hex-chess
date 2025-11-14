from typing import Tuple, Optional, Dict
import math
from constants import *

class HexTile:
    """Represents a single hexagonal tile."""
    
    def __init__(self, q: int, r: int, color: Tuple[int, int, int]):
        self.q = q
        self.r = r
        self.color = color
        self.piece = None  # Will hold (color, piece_name) tuple
        self.pixel_pos = None  # Will be set during rendering
        
    def set_piece(self, color: str, piece_name: str):
        """Place a piece on this tile."""
        self.piece = (color, piece_name)
        
    def remove_piece(self):
        """Remove piece from this tile."""
        self.piece = None
        
    def has_piece(self) -> bool:
        """Check if tile has a piece."""
        return self.piece is not None
    
    def get_piece(self) -> Optional[Tuple[str, str]]:
        """Get the piece on this tile."""
        return self.piece


class HexBoard:
    """Represents a hexagonal chess board using axial coordinates."""
    
    def __init__(self, size: int, hex_radius: float):
        self.size = size
        self.radius = hex_radius
        self.tiles: Dict[Tuple[int, int], HexTile] = {}
        self.current_turn = "white"  # Track whose turn it is
        self._generate_tiles()
        
    def _generate_tiles(self):
        """Generate hex tiles using axial coordinates (q, r)."""
        for q in range(-self.size + 1, self.size):
            r1 = max(-self.size + 1, -q - self.size + 1)
            r2 = min(self.size - 1, -q + self.size - 1)
            for r in range(r1, r2 + 1):
                color = self._get_hex_color(q, r)
                self.tiles[(q, r)] = HexTile(q, r, color)
    
    def _get_hex_color(self, q: int, r: int) -> Tuple[int, int, int]:
        """
        Determine hex color using 3-coloring algorithm.
        For hexagonal grids, we can use: (q - r) mod 3
        This ensures no two adjacent hexagons have the same color.
        """
        color_index = (q - r) % 3
        colors = [GREY, WHITE, BLACK]
        return colors[color_index]
    
    def axial_to_pixel(self, q: int, r: int, center_x: float, center_y: float) -> Tuple[float, float]:
        """Convert axial coordinates to pixel coordinates."""
        x = center_x + self.radius * (3/2 * q)
        y = center_y + self.radius * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
        return x, y
    
    def pixel_to_axial(self, x: float, y: float, center_x: float, center_y: float) -> Optional[Tuple[int, int]]:
        """Convert pixel coordinates to axial coordinates."""
        # Convert to fractional axial coordinates
        x_rel = x - center_x
        y_rel = y - center_y
        
        q = (2.0/3.0 * x_rel) / self.radius
        r = (-1.0/3.0 * x_rel + math.sqrt(3)/3 * y_rel) / self.radius
        
        # Round to nearest hex
        return self._axial_round(q, r)
    
    def _axial_round(self, q: float, r: float) -> Optional[Tuple[int, int]]:
        """Round fractional axial coordinates to nearest hex."""
        s = -q - r
        
        q_int = round(q)
        r_int = round(r)
        s_int = round(s)
        
        q_diff = abs(q_int - q)
        r_diff = abs(r_int - r)
        s_diff = abs(s_int - s)
        
        if q_diff > r_diff and q_diff > s_diff:
            q_int = -r_int - s_int
        elif r_diff > s_diff:
            r_int = -q_int - s_int
        
        # Check if this coordinate is on the board
        if (q_int, r_int) in self.tiles:
            return (q_int, r_int)
        return None
    
    def get_tile(self, q: int, r: int) -> Optional[HexTile]:
        """Get tile at given axial coordinates."""
        return self.tiles.get((q, r))
    
    def place_piece(self, q: int, r: int, color: str, piece_name: str) -> bool:
        """Place a piece on the board."""
        tile = self.get_tile(q, r)
        if tile:
            tile.set_piece(color, piece_name)
            return True
        return False
    
    def move_piece(self, from_q: int, from_r: int, to_q: int, to_r: int) -> bool:
        """Move a piece from one tile to another."""
        from_tile = self.get_tile(from_q, from_r)
        to_tile = self.get_tile(to_q, to_r)
        
        if not from_tile or not to_tile or not from_tile.has_piece() or from_tile == to_tile:
            return False
        
        piece_color, _ = from_tile.get_piece()
        
        # Check if it's this color's turn
        if piece_color != self.current_turn:
            return False
        
        # Make the move
        to_tile.piece = from_tile.piece
        from_tile.remove_piece()
        
        # Switch turns
        self.current_turn = "black" if self.current_turn == "white" else "white"
        return True
    
    def get_hex_corners(self, center_x: float, center_y: float) -> list:
        """Calculate the six corner points of a hexagon."""
        corners = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.pi / 180 * angle_deg
            x = center_x + self.radius * math.cos(angle_rad)
            y = center_y + self.radius * math.sin(angle_rad)
            corners.append((x, y))
        return corners
    
    def get_neighbors(self, q: int, r: int) -> list:
        """Get all six neighboring hex coordinates."""
        # Six directions in axial coordinates
        directions = [
            (1, 0), (1, -1), (0, -1),
            (-1, 0), (-1, 1), (0, 1)
        ]
        neighbors = []
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            if (nq, nr) in self.tiles:
                neighbors.append((nq, nr))
        return neighbors
    
    def get_legal_moves(self, q: int, r: int) -> list:
        """Get all legal moves for a piece at the given position."""
        tile = self.get_tile(q, r)
        if not tile or not tile.has_piece():
            return []
        
        piece_color, piece_name = tile.get_piece()
        
        # Only show legal moves if it's this piece's turn
        if piece_color != self.current_turn:
            return []
        
        if piece_name == "pawn":
            return self._get_pawn_moves(q, r, piece_color)
        elif piece_name == "knight":
            return self._get_knight_moves(q, r, piece_color)
        elif piece_name == "bishop":
            return self._get_bishop_moves(q, r, piece_color)
        elif piece_name == "rook":
            return self._get_rook_moves(q, r, piece_color)
        elif piece_name == "queen":
            return self._get_queen_moves(q, r, piece_color)
        elif piece_name == "king":
            return self._get_king_moves(q, r, piece_color)
        
        return []
    
    def _get_pawn_moves(self, q: int, r: int, color: str) -> list:
        """Get legal pawn moves (Gliński's hexagonal chess rules).
        
        Pawns move straight forward (in ONE direction only) without capturing.
        They capture obliquely forward to adjacent hexes (in rook/orthogonal directions).
        Pawns can move 2 spaces ONLY from their exact initial starting position.
        
        White pawns move toward negative r (toward black's side).
        Black pawns move toward positive r (toward white's side).
        """
        moves = []
        
        # Define exact starting positions for each pawn based on initial setup
        white_pawn_starts = [
            (-4, 5), (-3, 4), (-2, 3), (-1, 2), (0, 1),
            (1, 1), (2, 1), (3, 1), (4, 1)
        ]
        black_pawn_starts = [
            (4, -5), (3, -4), (2, -3), (1, -2), (0, -1),
            (-1, -1), (-2, -1), (-3, -1), (-4, -1)
        ]
        
        # Determine forward direction and check if at exact starting position
        if color == "white":
            # White moves straight forward: toward negative r
            forward_dir = (0, -1)
            # Check if this pawn is at its EXACT starting position
            is_starting_position = (q, r) in white_pawn_starts
            # Capture directions: obliquely forward (adjacent hexes in rook directions)
            capture_dirs = [(-1, 0), (1, -1)]
        else:
            # Black moves straight forward: toward positive r
            forward_dir = (0, 1)
            # Check if this pawn is at its EXACT starting position
            is_starting_position = (q, r) in black_pawn_starts
            # Capture directions: obliquely forward
            capture_dirs = [(1, 0), (-1, 1)]
        
        # Single step forward (only if empty)
        nq, nr = q + forward_dir[0], r + forward_dir[1]
        target = self.get_tile(nq, nr)
        if target and not target.has_piece():
            moves.append((nq, nr))
            
            # Two-step initial move (only if first move is clear AND at exact starting position)
            if is_starting_position:
                nq2, nr2 = q + forward_dir[0] * 2, r + forward_dir[1] * 2
                target2 = self.get_tile(nq2, nr2)
                if target2 and not target2.has_piece():
                    moves.append((nq2, nr2))
        
        # Capture moves (obliquely forward - orthogonal/rook directions only)
        for dq, dr in capture_dirs:
            nq, nr = q + dq, r + dr
            target = self.get_tile(nq, nr)
            if target and target.has_piece():
                enemy_color, _ = target.get_piece()
                if enemy_color != color:
                    moves.append((nq, nr))
        
        return moves
    
    def _get_knight_moves(self, q: int, r: int, color: str) -> list:
        """Get legal knight moves (Gliński's rules).
        
        Knight moves in an 'L' shape: 
        - Two spaces in one orthogonal direction
        - Then one space in an adjacent orthogonal direction (60° angle)
        - Jumps over intervening pieces
        """
        moves = []
        
        # Six orthogonal directions for the initial 2-step move
        orthogonal_dirs = [
            (1, 0), (-1, 0),      # Along q-axis
            (0, 1), (0, -1),      # Along r-axis
            (1, -1), (-1, 1)      # Along s-axis
        ]
        
        # For each direction, move 2 steps, then 1 step in adjacent directions
        for dq, dr in orthogonal_dirs:
            # Move 2 steps in this direction
            mid_q, mid_r = q + 2*dq, r + 2*dr
            
            # Find the two adjacent orthogonal directions (60° angles)
            # For each base direction, there are 2 adjacent orthogonal directions
            if (dq, dr) == (1, 0):      # +q direction
                perpendicular = [(0, 1), (1, -1)]
            elif (dq, dr) == (-1, 0):   # -q direction
                perpendicular = [(0, -1), (-1, 1)]
            elif (dq, dr) == (0, 1):    # +r direction
                perpendicular = [(-1, 1), (1, 0)]
            elif (dq, dr) == (0, -1):   # -r direction
                perpendicular = [(1, -1), (-1, 0)]
            elif (dq, dr) == (1, -1):   # +s direction (q+1, r-1)
                perpendicular = [(1, 0), (0, -1)]
            else:  # (-1, 1)            # -s direction (q-1, r+1)
                perpendicular = [(-1, 0), (0, 1)]
            
            # Try both perpendicular directions
            for pq, pr in perpendicular:
                nq, nr = mid_q + pq, mid_r + pr
                target = self.get_tile(nq, nr)
                
                if target:
                    if not target.has_piece():
                        moves.append((nq, nr))
                    else:
                        enemy_color, _ = target.get_piece()
                        if enemy_color != color:
                            moves.append((nq, nr))
        
        return moves
    
    def _get_sliding_moves(self, q: int, r: int, color: str, directions: list) -> list:
        """Helper for sliding pieces (bishop, rook, queen)."""
        moves = []
        
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            
            # Keep sliding in this direction until blocked
            while (nq, nr) in self.tiles:
                target = self.get_tile(nq, nr)
                
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    # Blocked by piece
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))  # Can capture
                    break  # Stop sliding
                
                nq += dq
                nr += dr
        
        return moves
    
    def _get_bishop_moves(self, q: int, r: int, color: str) -> list:
        """Get legal bishop moves.
        
        Bishops move along diagonals of the same color.
        In 3-colored hexagonal chess, bishops stay on their color.
        """
        moves = []
        current_tile = self.get_tile(q, r)
        if not current_tile:
            return moves
        
        target_color = current_tile.color
        
        # Six diagonal directions that preserve color in 3-coloring
        diagonal_dirs = [
            (1, 1), (-1, -1),     # Main diagonal
            (2, -1), (-2, 1),     # Second diagonal  
            (1, -2), (-1, 2)      # Third diagonal
        ]
        
        for dq, dr in diagonal_dirs:
            nq, nr = q + dq, r + dr
            
            # Keep moving in this direction while same color
            while (nq, nr) in self.tiles:
                target = self.get_tile(nq, nr)
                
                # Check if still same color
                if target.color != target_color:
                    break
                
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    # Blocked by piece
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))  # Can capture
                    break  # Stop sliding
                
                nq += dq
                nr += dr
        
        return moves
    
    def _get_rook_moves(self, q: int, r: int, color: str) -> list:
        """Get legal rook moves.
        
        Rooks move in straight lines along the 6 hex directions.
        """
        # Rooks move in 6 straight orthogonal directions
        orthogonal_dirs = [
            (1, 0), (-1, 0),      # Along q-axis
            (0, 1), (0, -1),      # Along r-axis
            (1, -1), (-1, 1)      # Along s-axis (where s = -q - r)
        ]
        return self._get_sliding_moves(q, r, color, orthogonal_dirs)
    
    def _get_queen_moves(self, q: int, r: int, color: str) -> list:
        """Get legal queen moves.
        
        Queen combines rook and bishop movements.
        """
        rook_moves = self._get_rook_moves(q, r, color)
        bishop_moves = self._get_bishop_moves(q, r, color)
        
        # Combine and remove duplicates
        all_moves = list(set(rook_moves + bishop_moves))
        return all_moves
    
    def _get_king_moves(self, q: int, r: int, color: str) -> list:
        """Get legal king moves.
        
        King moves one hex in any direction:
        - 6 orthogonal directions (rook-like)
        - 6 diagonal directions to same-colored hexes (bishop-like)
        """
        moves = []
        current_tile = self.get_tile(q, r)
        if not current_tile:
            return moves
        
        target_color = current_tile.color
        
        # Orthogonal (rook-like) - one step
        orthogonal_dirs = [
            (1, 0), (-1, 0),
            (0, 1), (0, -1),
            (1, -1), (-1, 1)
        ]
        
        # Diagonal (bishop-like) - one step to same color
        diagonal_dirs = [
            (1, 1), (-1, -1),
            (2, -1), (-2, 1),
            (1, -2), (-1, 2)
        ]
        
        # Check orthogonal moves
        for dq, dr in orthogonal_dirs:
            nq, nr = q + dq, r + dr
            target = self.get_tile(nq, nr)
            
            if target:
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))
        
        # Check diagonal moves (only to same color)
        for dq, dr in diagonal_dirs:
            nq, nr = q + dq, r + dr
            target = self.get_tile(nq, nr)
            
            if target and target.color == target_color:
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))
        
        return moves
    
    def find_king(self, color: str) -> Optional[Tuple[int, int]]:
        """Find the position of a king of the given color."""
        for (q, r), tile in self.tiles.items():
            if tile.has_piece():
                piece_color, piece_name = tile.get_piece()
                if piece_color == color and piece_name == "king":
                    return (q, r)
        return None
    
    def is_square_attacked(self, q: int, r: int, by_color: str) -> bool:
        """Check if a square is attacked by any piece of the given color."""
        # Check all tiles for enemy pieces that can attack this square
        for (pq, pr), tile in self.tiles.items():
            if not tile.has_piece():
                continue
            
            piece_color, piece_name = tile.get_piece()
            if piece_color != by_color:
                continue
            
            # Get moves for this piece (temporarily)
            possible_moves = []
            if piece_name == "pawn":
                # For pawns, only check capture moves
                if piece_color == "white":
                    capture_dirs = [(-1, 0), (1, -1)]
                else:
                    capture_dirs = [(1, 0), (-1, 1)]
                
                for dq, dr in capture_dirs:
                    nq, nr = pq + dq, pr + dr
                    if (nq, nr) == (q, r):
                        return True
            elif piece_name == "knight":
                possible_moves = self._get_knight_moves(pq, pr, piece_color)
            elif piece_name == "bishop":
                possible_moves = self._get_bishop_moves(pq, pr, piece_color)
            elif piece_name == "rook":
                possible_moves = self._get_rook_moves(pq, pr, piece_color)
            elif piece_name == "queen":
                possible_moves = self._get_queen_moves(pq, pr, piece_color)
            elif piece_name == "king":
                possible_moves = self._get_king_moves(pq, pr, piece_color)
            
            if (q, r) in possible_moves:
                return True
        
        return False
    
    def is_in_check(self, color: str) -> bool:
        """Check if the king of the given color is in check."""
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        
        enemy_color = "black" if color == "white" else "white"
        return self.is_square_attacked(king_pos[0], king_pos[1], enemy_color)
    
    def simulate_move(self, from_q: int, from_r: int, to_q: int, to_r: int) -> bool:
        """Simulate a move and check if it leaves the king in check.
        Returns True if the move is valid (doesn't leave king in check)."""
        from_tile = self.get_tile(from_q, from_r)
        to_tile = self.get_tile(to_q, to_r)
        
        if not from_tile or not to_tile or not from_tile.has_piece():
            return False
        
        # Save the state
        moving_piece = from_tile.piece
        captured_piece = to_tile.piece
        piece_color, _ = moving_piece
        
        # Make the move temporarily
        to_tile.piece = moving_piece
        from_tile.piece = None
        
        # Check if king is in check
        in_check = self.is_in_check(piece_color)
        
        # Restore the state
        from_tile.piece = moving_piece
        to_tile.piece = captured_piece
        
        return not in_check
    
    def get_legal_moves_with_check(self, q: int, r: int) -> list:
        """Get legal moves that don't leave the king in check."""
        raw_moves = self.get_legal_moves(q, r)
        legal_moves = []
        
        for move_q, move_r in raw_moves:
            if self.simulate_move(q, r, move_q, move_r):
                legal_moves.append((move_q, move_r))
        
        return legal_moves
    
    def has_any_legal_moves(self, color: str) -> bool:
        """Check if a color has any legal moves."""
        for (q, r), tile in self.tiles.items():
            if not tile.has_piece():
                continue
            
            piece_color, _ = tile.get_piece()
            if piece_color != color:
                continue
            
            # Check if this piece has any legal moves
            moves = self.get_legal_moves_with_check(q, r)
            if moves:
                return True
        
        return False
    
    def is_checkmate(self, color: str) -> bool:
        """Check if the given color is in checkmate."""
        return self.is_in_check(color) and not self.has_any_legal_moves(color)
    
    def is_stalemate(self, color: str) -> bool:
        """Check if the given color is in stalemate."""
        return not self.is_in_check(color) and not self.has_any_legal_moves(color)
    
    def get_game_status(self) -> str:
        """Get the current game status.
        Returns: 'check', 'checkmate', 'stalemate', 'draw', or 'active'
        """
        current_color = self.current_turn
        
        if self.is_checkmate(current_color):
            return 'checkmate'
        
        if self.is_stalemate(current_color):
            return 'stalemate'
        
        if self.is_in_check(current_color):
            return 'check'
        
        # TODO: Add draw by repetition, 50-move rule, insufficient material
        
        return 'active'
