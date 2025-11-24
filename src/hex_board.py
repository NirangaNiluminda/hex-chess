from typing import Tuple, Optional, Dict
import math
from constants import *
from game import MoveGenerator

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
        self.flipped = False
        self.en_passant_target = None
        self.pending_promotion = None
        self.captured_pieces = {"white": [], "black": []}
        self._generate_tiles()
        self.move_generator = MoveGenerator(self)
        
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
        
        piece_color,piece_name = from_tile.get_piece()
        
        # Check if it's this color's turn
        if piece_color != self.current_turn:
            return False
        
        # Track captured piece before removing it
        if to_tile.has_piece():
            captured_color, captured_piece = to_tile.get_piece()
            self.captured_pieces[captured_color].append(captured_piece)
        # Handle en-passant capture
        if piece_name == "pawn" and (to_q, to_r) == self.en_passant_target:
        # Remove the captured pawn
            if piece_color == "white":
                captured_pawn_pos = (to_q, to_r + 1)  # Black pawn is one square "below"
            else:
                captured_pawn_pos = (to_q, to_r - 1)  # White pawn is one square "above"
        
            captured_tile = self.get_tile(*captured_pawn_pos)
            if captured_tile:
                # track en passant capture
                captured_color, captured_piece = captured_tile.get_piece()
                self.captured_pieces[captured_color].append(captured_piece)
                captured_tile.remove_piece()

        # Clear en-passant target before checking for new two-square pawn moves
        self.en_passant_target = None

        # Check if this is a two-square pawn move (sets new en-passant target)
        if piece_name == "pawn":
            white_pawn_starts = [
                (-4, 5), (-3, 4), (-2, 3), (-1, 2), (0, 1),
                (1, 1), (2, 1), (3, 1), (4, 1)
            ]
            black_pawn_starts = [
                (4, -5), (3, -4), (2, -3), (1, -2), (0, -1),
                (-1, -1), (-2, -1), (-3, -1), (-4, -1)
            ]
        
            if piece_color == "white" and (from_q, from_r) in white_pawn_starts:
                # Check if moved two squares
                if to_r == from_r - 2:
                    self.en_passant_target = (from_q, from_r - 1)
            elif piece_color == "black" and (from_q, from_r) in black_pawn_starts:
                # Check if moved two squares
                if to_r == from_r + 2:
                    self.en_passant_target = (from_q, from_r + 1)
        # Make the move
        to_tile.piece = from_tile.piece
        from_tile.remove_piece()
        
        # Check for pawn promotion - ADD THIS BLOCK
        if piece_name == "pawn" and self.is_promotion_square(to_q, to_r, piece_color):
            self.pending_promotion = (to_q, to_r, piece_color)
            # Don't switch turns yet - wait for promotion choice
            return True
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
    
    def toggle_flip(self):
        """Toggle the visual flipped state of the board."""
        self.flipped = not self.flipped
    
    def is_promotion_square(self, q: int, r: int, color: str) -> bool:
        """Check if a square is in the promotion zone for the given color."""
        # White pawns promote on black's back rank
        if color == "white":
            # Black's back rank positions
            black_back_rank = [
            (4, -5), (3, -5), (2, -5), (1, -5), (0, -5),
            (-1, -4), (-2, -3), (-3, -2), (-4, -1)
        ]
            return (q, r) in black_back_rank
        else:
            # Black pawns promote on white's back rank
            white_back_rank = [
            (-4, 5), (-3, 5), (-2, 5), (-1, 5), (0, 5),
            (1, 4), (2, 3), (3, 2), (4, 1)
            ]
            return (q, r) in white_back_rank
    
    def promote_pawn(self, piece_name: str) -> bool:
        """Promote the pending pawn to the specified piece."""
        if not self.pending_promotion:
            return False
        
        q, r, color = self.pending_promotion
        tile = self.get_tile(q, r)
        
        if not tile:
            return False
        
        # Replace pawn with chosen piece
        tile.set_piece(color, piece_name)
        
        # Clear promotion state
        self.pending_promotion = None
        
        # Now switch turns
        self.current_turn = "black" if self.current_turn == "white" else "white"
        
        return True


class HexGeometry:
    """Geometric calculations for hexagonal boards."""
    
    @staticmethod
    def axial_distance(q1: int, r1: int, q2: int, r2: int) -> int:
        """Calculate distance between two hexagons in axial coordinates."""
        return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2
    
    @staticmethod
    def distance_from_center(q: int, r: int) -> int:
        """Calculate distance from board center (0, 0)."""
        return HexGeometry.axial_distance(q, r, 0, 0)
    
    @staticmethod
    def distance_from_edge(q: int, r: int, board_size: int = 5) -> int:
        """Calculate minimum distance to board edge."""
        s = -q - r
        max_coord = max(abs(q), abs(r), abs(s))
        return board_size - 1 - max_coord
    
    @staticmethod
    def get_rank(q: int, r: int, color: str, board_size: int = 5) -> int:
        """
        Get the 'rank' (distance from own back rank) for a piece.
        Returns 0 at back rank, increases toward opponent.
        
        We calculate this by finding the maximum r-value on the board
        and measuring distance from there.
        """
        if color == 'white':
            # White advances by decreasing r
            # Maximum r for a size-5 board is 4 (at the edges)
            # But from the actual board data, white pieces go up to r=5
            # So white's back rank appears to be at r=5
            # Rank = 5 - r gives: r=5 -> rank 0, r=4 -> rank 1, etc.
            max_r = board_size  # 5 for size-5 board
            return max_r - r
        else:
            # Black advances by increasing r  
            # Black's back rank is at r=-5
            # Rank = 5 + r gives: r=-5 -> rank 0, r=-4 -> rank 1, etc.
            max_r = board_size  # 5 for size-5 board
            return max_r + r
    
    @staticmethod
    def get_file_centrality(q: int, board_size: int = 5) -> int:
        """
        Get how central the file (q coordinate) is.
        Returns 0 at edges, higher toward center.
        """
        return board_size - 1 - abs(q)