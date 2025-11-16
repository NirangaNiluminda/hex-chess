from typing import Tuple, List, Optional

class MoveGenerator:
    """Encapsulates move-generation and attack detection for a HexBoard.

    Expects a board-like object with:
      - tiles: Dict[(q,r) -> HexTile]
      - get_tile(q,r)
      - current_turn
    """

    def __init__(self, board):
        self.board = board

    def get_legal_moves(self, q: int, r: int) -> List[Tuple[int, int]]:
        tile = self.board.get_tile(q, r)
        if not tile or not tile.has_piece():
            return []

        piece_color, piece_name = tile.get_piece()

        # Only show legal moves if it's this piece's turn
        if piece_color != self.board.current_turn:
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

    def _get_pawn_moves(self, q: int, r: int, color: str):
        moves = []

        white_pawn_starts = [
            (-4, 5), (-3, 4), (-2, 3), (-1, 2), (0, 1),
            (1, 1), (2, 1), (3, 1), (4, 1)
        ]
        black_pawn_starts = [
            (4, -5), (3, -4), (2, -3), (1, -2), (0, -1),
            (-1, -1), (-2, -1), (-3, -1), (-4, -1)
        ]

        if color == "white":
            forward_dir = (0, -1)
            is_starting_position = (q, r) in white_pawn_starts
            capture_dirs = [(-1, 0), (1, -1)]
        else:
            forward_dir = (0, 1)
            is_starting_position = (q, r) in black_pawn_starts
            capture_dirs = [(1, 0), (-1, 1)]

        nq, nr = q + forward_dir[0], r + forward_dir[1]
        target = self.board.get_tile(nq, nr)
        if target and not target.has_piece():
            moves.append((nq, nr))
            if is_starting_position:
                nq2, nr2 = q + forward_dir[0] * 2, r + forward_dir[1] * 2
                target2 = self.board.get_tile(nq2, nr2)
                if target2 and not target2.has_piece():
                    moves.append((nq2, nr2))

        for dq, dr in capture_dirs:
            nq, nr = q + dq, r + dr
            target = self.board.get_tile(nq, nr)
            if target and target.has_piece():
                enemy_color, _ = target.get_piece()
                if enemy_color != color:
                    moves.append((nq, nr))
        if self.board.en_passant_target:
            for dq, dr in capture_dirs:
                nq, nr = q + dq, r + dr
                if (nq, nr) == self.board.en_passant_target:
                    moves.append((nq, nr))
        return moves

    def _get_knight_moves(self, q: int, r: int, color: str):
        moves = []
        orthogonal_dirs = [
            (1, 0), (-1, 0),
            (0, 1), (0, -1),
            (1, -1), (-1, 1)
        ]
        for dq, dr in orthogonal_dirs:
            mid_q, mid_r = q + 2*dq, r + 2*dr

            if (dq, dr) == (1, 0):
                perpendicular = [(0, 1), (1, -1)]
            elif (dq, dr) == (-1, 0):
                perpendicular = [(0, -1), (-1, 1)]
            elif (dq, dr) == (0, 1):
                perpendicular = [(-1, 1), (1, 0)]
            elif (dq, dr) == (0, -1):
                perpendicular = [(1, -1), (-1, 0)]
            elif (dq, dr) == (1, -1):
                perpendicular = [(1, 0), (0, -1)]
            else:
                perpendicular = [(-1, 0), (0, 1)]

            for pq, pr in perpendicular:
                nq, nr = mid_q + pq, mid_r + pr
                target = self.board.get_tile(nq, nr)
                if target:
                    if not target.has_piece():
                        moves.append((nq, nr))
                    else:
                        enemy_color, _ = target.get_piece()
                        if enemy_color != color:
                            moves.append((nq, nr))
        return moves

    def _get_sliding_moves(self, q: int, r: int, color: str, directions):
        moves = []
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            while (nq, nr) in self.board.tiles:
                target = self.board.get_tile(nq, nr)
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))
                    break
                nq += dq
                nr += dr
        return moves

    def _get_bishop_moves(self, q: int, r: int, color: str):
        moves = []
        current_tile = self.board.get_tile(q, r)
        if not current_tile:
            return moves
        target_color = current_tile.color
        diagonal_dirs = [
            (1, 1), (-1, -1),
            (2, -1), (-2, 1),
            (1, -2), (-1, 2)
        ]
        for dq, dr in diagonal_dirs:
            nq, nr = q + dq, r + dr
            while (nq, nr) in self.board.tiles:
                target = self.board.get_tile(nq, nr)
                if target.color != target_color:
                    break
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))
                    break
                nq += dq
                nr += dr
        return moves

    def _get_rook_moves(self, q: int, r: int, color: str):
        orthogonal_dirs = [
            (1, 0), (-1, 0),
            (0, 1), (0, -1),
            (1, -1), (-1, 1)
        ]
        return self._get_sliding_moves(q, r, color, orthogonal_dirs)

    def _get_queen_moves(self, q: int, r: int, color: str):
        rook_moves = self._get_rook_moves(q, r, color)
        bishop_moves = self._get_bishop_moves(q, r, color)
        return list(set(rook_moves + bishop_moves))

    def _get_king_moves(self, q: int, r: int, color: str):
        moves = []
        current_tile = self.board.get_tile(q, r)
        if not current_tile:
            return moves
        target_color = current_tile.color
        orthogonal_dirs = [
            (1, 0), (-1, 0),
            (0, 1), (0, -1),
            (1, -1), (-1, 1)
        ]
        diagonal_dirs = [
            (1, 1), (-1, -1),
            (2, -1), (-2, 1),
            (1, -2), (-1, 2)
        ]
        for dq, dr in orthogonal_dirs:
            nq, nr = q + dq, r + dr
            target = self.board.get_tile(nq, nr)
            if target:
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))
        for dq, dr in diagonal_dirs:
            nq, nr = q + dq, r + dr
            target = self.board.get_tile(nq, nr)
            if target and target.color == target_color:
                if not target.has_piece():
                    moves.append((nq, nr))
                else:
                    enemy_color, _ = target.get_piece()
                    if enemy_color != color:
                        moves.append((nq, nr))
        return moves

    def is_square_attacked(self, q: int, r: int, by_color: str) -> bool:
        for (pq, pr), tile in self.board.tiles.items():
            if not tile.has_piece():
                continue
            piece_color, piece_name = tile.get_piece()
            if piece_color != by_color:
                continue
            if piece_name == "pawn":
                if piece_color == "white":
                    capture_dirs = [(-1, 0), (1, -1)]
                else:
                    capture_dirs = [(1, 0), (-1, 1)]
                for dq, dr in capture_dirs:
                    if (pq + dq, pr + dr) == (q, r):
                        return True
            else:
                if piece_name == "knight":
                    moves = self._get_knight_moves(pq, pr, piece_color)
                elif piece_name == "bishop":
                    moves = self._get_bishop_moves(pq, pr, piece_color)
                elif piece_name == "rook":
                    moves = self._get_rook_moves(pq, pr, piece_color)
                elif piece_name == "queen":
                    moves = self._get_queen_moves(pq, pr, piece_color)
                elif piece_name == "king":
                    moves = self._get_king_moves(pq, pr, piece_color)
                else:
                    moves = []
                if (q, r) in moves:
                    return True
        return False

class MoveValidator:
    def __init__(self, board):
        self.board = board
        self.move_generator = MoveGenerator(board)

    def get_legal_moves(self, q: int, r: int) -> list:
        """Delegate move generation to MoveGenerator."""
        return self.move_generator.get_legal_moves(q, r)
    
    def is_square_attacked(self, q: int, r: int, by_color: str) -> bool:
        """Delegate attack detection to MoveGenerator."""
        return self.move_generator.is_square_attacked(q, r, by_color)   
    
    def find_king(self, color: str) -> Optional[Tuple[int, int]]:
        """Find the position of a king of the given color."""
        for (q, r), tile in self.board.tiles.items():
            if tile.has_piece():
                piece_color, piece_name = tile.get_piece()
                if piece_color == color and piece_name == "king":
                    return (q, r)
        return None
    
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
        from_tile = self.board.get_tile(from_q, from_r)  # Fixed: use self.board
        to_tile = self.board.get_tile(to_q, to_r)        # Fixed: use self.board
        
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
        for (q, r), tile in self.board.tiles.items():  # Fixed: use self.board.tiles
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
        current_color = self.board.current_turn
        
        if self.is_checkmate(current_color):
            return 'checkmate'
        
        if self.is_stalemate(current_color):
            return 'stalemate'
        
        if self.is_in_check(current_color):
            return 'check'
        
        # TODO: Add draw by repetition, 50-move rule, insufficient material
        
        return 'active'
