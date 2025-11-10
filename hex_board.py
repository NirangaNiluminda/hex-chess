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
        
        if from_tile and to_tile and from_tile.has_piece() and from_tile != to_tile:
            to_tile.piece = from_tile.piece
            from_tile.remove_piece()
            return True
        return False
    
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
        """Get legal pawn moves (forward one hex, capture diagonally forward)."""
        moves = []
        
        # Pawns move "forward" toward opponent
        # White moves toward negative r, black moves toward positive r
        if color == "white":
            # Forward moves (3 directions toward black side)
            forward_dirs = [(0, -1), (1, -1), (-1, 0)]
            # Capture diagonally forward
            capture_dirs = [(1, -1), (-1, 0)]
        else:
            # Black moves opposite
            forward_dirs = [(0, 1), (-1, 1), (1, 0)]
            capture_dirs = [(-1, 1), (1, 0)]
        
        # Forward move (only if empty)
        for dq, dr in forward_dirs:
            nq, nr = q + dq, r + dr
            target = self.get_tile(nq, nr)
            if target and not target.has_piece():
                moves.append((nq, nr))
        
        # Capture moves (only if enemy piece)
        for dq, dr in capture_dirs:
            nq, nr = q + dq, r + dr
            target = self.get_tile(nq, nr)
            if target and target.has_piece():
                enemy_color, _ = target.get_piece()
                if enemy_color != color:
                    moves.append((nq, nr))
        
        return moves
    
    def _get_knight_moves(self, q: int, r: int, color: str) -> list:
        """Get legal knight moves (one diagonal + one straight outward = 12 circular positions).
        
        Knight movement: Move one field diagonally (to same color), then one field 
        straight outward. This creates 12 destination fields in a circular pattern.
        """
        moves = []
        current_tile = self.get_tile(q, r)
        if not current_tile:
            return moves
        
        # Knight moves: one diagonal (same color) + one straight outward
        # There are 6 diagonal directions and from each, 2 outward directions
        
        # Pattern: (diagonal_dq, diagonal_dr) -> [(out_dq1, out_dr1), (out_dq2, out_dr2)]
        knight_patterns = [
            # From (1,1) diagonal, go out in two directions
            ((1, 1), [(1, 0), (0, 1)]),       # -> (2,1), (1,2)
            # From (-1,-1) diagonal
            ((-1, -1), [(-1, 0), (0, -1)]),   # -> (-2,-1), (-1,-2)
            # From (2,-1) diagonal
            ((2, -1), [(1, 0), (1, -1)]),     # -> (3,-1), (3,-2)
            # From (-2,1) diagonal
            ((-2, 1), [(-1, 0), (-1, 1)]),    # -> (-3,1), (-3,2)
            # From (1,-2) diagonal
            ((1, -2), [(0, -1), (1, -1)]),    # -> (1,-3), (2,-3)
            # From (-1,2) diagonal
            ((-1, 2), [(0, 1), (-1, 1)]),     # -> (-1,3), (-2,3)
        ]
        
        for (diag_dq, diag_dr), out_dirs in knight_patterns:
            for out_dq, out_dr in out_dirs:
                # Final position: diagonal + outward
                nq = q + diag_dq + out_dq
                nr = r + diag_dr + out_dr
                
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
        """Get legal bishop moves (along same-colored diagonal lines).
        
        In hex chess, bishops move along their color. Since we use 3-coloring
        based on (q - r) mod 3, bishops move in directions that preserve this value.
        The three color-preserving diagonal directions are based on the color index.
        """
        moves = []
        current_tile = self.get_tile(q, r)
        if not current_tile:
            return moves
        
        target_color = current_tile.color
        
        # Bishops move along lines of same color
        # For 3-coloring with (q - r) mod 3, same color means (q - r) stays constant mod 3
        # This gives us 3 main diagonal directions
        
        # Direction 1: Move along q-r constant (diagonal)
        diagonal_dirs = [
            (1, 1),   # q+1, r+1 keeps q-r same
            (-1, -1), # q-1, r-1 keeps q-r same
            (2, -1),  # q+2, r-1 changes q-r by 3
            (-2, 1),  # q-2, r+1 changes q-r by -3
            (1, -2),  # q+1, r-2 changes q-r by 3
            (-1, 2),  # q-1, r+2 changes q-r by -3
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
        """Get legal rook moves (6 orthogonal/straight directions)."""
        # Rooks move in 6 straight lines (the 6 neighbor directions)
        orthogonal_dirs = [
            (1, 0), (-1, 0),    # Along q-axis
            (0, 1), (0, -1),    # Along r-axis
            (1, -1), (-1, 1)    # Along s-axis (where s = -q - r)
        ]
        return self._get_sliding_moves(q, r, color, orthogonal_dirs)
    
    def _get_queen_moves(self, q: int, r: int, color: str) -> list:
        """Get legal queen moves (combination of rook + bishop moves)."""
        # Queen combines both rook and bishop movements
        rook_moves = self._get_rook_moves(q, r, color)
        bishop_moves = self._get_bishop_moves(q, r, color)
        
        # Combine and remove duplicates
        all_moves = list(set(rook_moves + bishop_moves))
        return all_moves
    
    def _get_king_moves(self, q: int, r: int, color: str) -> list:
        """Get legal king moves (one hex in any of 12 directions: 6 rook + 6 bishop).
        
        The king can move to:
        - 6 adjacent fields (rook directions) - share an edge
        - 6 diagonally adjacent same-colored fields (bishop directions) - share a vertex
        Total: 12 possible moves
        """
        moves = []
        current_tile = self.get_tile(q, r)
        if not current_tile:
            return moves
        
        target_color = current_tile.color
        
        # Rook directions (6 orthogonal neighbors - share an edge)
        rook_dirs = [
            (1, 0), (-1, 0),    # Along q-axis
            (0, 1), (0, -1),    # Along r-axis
            (1, -1), (-1, 1)    # Along s-axis
        ]
        
        # Bishop directions (6 diagonal same-color adjacent - share a vertex)
        # These are the 12 hexes around that share only a corner with current hex
        # But we only want the 6 that are same color
        all_second_ring = [
            (2, 0), (-2, 0),      # Along q-axis (distance 2)
            (0, 2), (0, -2),      # Along r-axis (distance 2)
            (2, -2), (-2, 2),     # Along s-axis (distance 2)
            (1, 1), (-1, -1),     # Diagonal pairs
            (2, -1), (-2, 1),     
            (1, -2), (-1, 2)
        ]
        
        # Find which of the surrounding hexes are same color and adjacent diagonally
        bishop_moves = []
        for dq, dr in all_second_ring:
            nq, nr = q + dq, r + dr
            target = self.get_tile(nq, nr)
            if target and target.color == target_color:
                # Check if it's truly adjacent (shares a vertex, not an edge)
                # Distance should be sqrt(3) in hex coordinates
                # For same color diagonal adjacents, we want specific patterns
                if (dq, dr) in [(1, 1), (-1, -1), (2, -1), (-2, 1), (1, -2), (-1, 2)]:
                    bishop_moves.append((dq, dr))
        
        # Check all rook directions (always valid if tile exists)
        for dq, dr in rook_dirs:
            nq, nr = q + dq, r + dr
            target = self.get_tile(nq, nr)
            
            if target:
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))
        
        # Check valid bishop directions
        for dq, dr in bishop_moves:
            nq, nr = q + dq, r + dr
            target = self.get_tile(nq, nr)
            
            if target:
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))
        
        return moves
