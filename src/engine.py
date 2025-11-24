import copy
from typing import Optional, Tuple, List
from game import MoveValidator
from evaluation import Evaluator
from constants import PIECE_VALUES

class ChessEngine:
    def __init__(self, board, depth):
        self.board = board
        # engine is white if board is flipped, otherwise black
        self.engine_color = 'white' if getattr(board, "flipped", False) else 'black'
        self.validator = MoveValidator(board)
        self.search_depth = depth
        self.nodes_searched = 0  # For debugging
        self.transposition_table = {}

    def _snapshot_board(self):
        """Return a snapshot of pieces & mutable board state to restore after simulation."""
        # snapshot pieces on tiles: map (q,r) -> piece or None
        pieces_snapshot = {}
        for coord, tile in self.board.tiles.items():
            # store a shallow copy of piece (tuple or None)
            pieces_snapshot[coord] = getattr(tile, "piece", None)
        # snapshot other relevant board-level state
        state_snapshot = {
            "current_turn": getattr(self.board, "current_turn", None),
            "en_passant_target": copy.deepcopy(getattr(self.board, "en_passant_target", None)),
            "pending_promotion": copy.deepcopy(getattr(self.board, "pending_promotion", None)),
            "captured_pieces": copy.deepcopy(getattr(self.board, "captured_pieces", {})),
        }
        return pieces_snapshot, state_snapshot

    def _restore_board(self, pieces_snapshot, state_snapshot):
        """Restore board to a previously captured snapshot."""
        # restore tile pieces
        for coord, piece in pieces_snapshot.items():
            tile = self.board.tiles.get(coord)
            if tile is None:
                continue
            # assign piece directly; if tile has helper methods you can also use them
            tile.piece = piece

        # restore board state
        self.board.current_turn = state_snapshot["current_turn"]
        self.board.en_passant_target = copy.deepcopy(state_snapshot["en_passant_target"])
        self.board.pending_promotion = copy.deepcopy(state_snapshot["pending_promotion"])
        self.board.captured_pieces = copy.deepcopy(state_snapshot["captured_pieces"])


    def _evaluate_engine_position(self) -> float:
        """
        Evaluate board and return a score oriented to the engine: higher == better for engine.
        Uses Evaluator.evaluate which returns (score, total_material, phase), where score positive favors white.
        For engine black we invert sign so engine always maximizes returned value.
        """
        score, total_mat, phase = Evaluator.evaluate(self.board)
        if self.engine_color == 'white':
            return score
        else:
            return -score

    def _order_moves(self, moves: List[Tuple[Tuple[int,int], Tuple[int,int]]], current_color: str) -> List[Tuple[Tuple[int,int], Tuple[int,int]]]:
        """
        Order moves to improve alpha-beta pruning efficiency.
        Priority: captures (MVV-LVA), then other moves.
        """
        def move_score(move):
            (from_q, from_r), (to_q, to_r) = move
            score = 0
            
            # Check if it's a capture
            to_tile = self.board.get_tile(to_q, to_r)
            if to_tile and to_tile.has_piece():
                victim_color, victim_name = to_tile.get_piece()
                if victim_color != current_color:
                    # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
                    from_tile = self.board.get_tile(from_q, from_r)
                    if from_tile and from_tile.has_piece():
                        _, attacker_name = from_tile.get_piece()
                        victim_value = PIECE_VALUES.get(victim_name, 0)
                        attacker_value = PIECE_VALUES.get(attacker_name, 0)
                        # Prioritize capturing high-value pieces with low-value pieces
                        score = victim_value * 10 - attacker_value
            
            # Small bonus for center moves
            center_dist = abs(to_q) + abs(to_r) + abs(-to_q - to_r)
            score -= center_dist
            
            return score
        
        # Sort moves by score (highest first)
        return sorted(moves, key=move_score, reverse=True)

    def _hash_position(self) -> str:
        """Create a simple hash of the current position."""
        pieces = []
        for (q, r), tile in sorted(self.board.tiles.items()):
            if tile and tile.has_piece():
                color, piece = tile.get_piece()
                pieces.append(f"{q},{r},{color},{piece}")
        return "|".join(pieces) + f"|{self.board.current_turn}"

    def _minimax(self, depth: int, is_maximizing: bool, alpha: float = float('-inf'), beta: float = float('inf')) -> float:
        """
        Minimax with alpha-beta pruning.
        is_maximizing: True if we're maximizing (engine's turn), False if minimizing (opponent's turn)
        Returns the best evaluation score from current position.
        """
        self.nodes_searched += 1
        # Create a simple position hash
        position_key = self._hash_position()
        
        # Check transposition table
        if position_key in self.transposition_table:
            cached_depth, cached_value = self.transposition_table[position_key]
            if cached_depth >= depth:
                return cached_value

        # Base case: reached max depth or game over
        if depth == 0:
            return self._evaluate_engine_position()

        current_turn = getattr(self.board, "current_turn", 'white')
        all_moves = []

        # Check if current player has any legal moves
        for (q, r), tile in self.board.tiles.items():
            if not tile or not tile.has_piece():
                continue
            piece_color, _ = tile.get_piece()
            if piece_color != current_turn:
                continue
            moves = self.validator.get_legal_moves_with_check(q, r)
            for (to_q, to_r) in moves:
                all_moves.append(((q, r), (to_q, to_r)))

        # If no moves available, return current evaluation (checkmate/stalemate)
        if not all_moves:
            eval_score = self._evaluate_engine_position()
            # Add mate detection bonus/penalty
            if self.validator.is_in_check(current_turn):
                # Checkmate - prefer faster mates
                eval_score = float('-inf') + depth if is_maximizing else float('inf') - depth
            return eval_score

        all_moves = self._order_moves(all_moves, current_turn)

        if is_maximizing:
            max_eval = float('-inf')
            for (from_q, from_r), (to_q, to_r) in all_moves:
                pieces_snap, state_snap = self._snapshot_board()
                self.board.move_piece(from_q, from_r, to_q, to_r)
                
                # Handle promotion
                if getattr(self.board, "pending_promotion", None):
                    pq, pr, pcolor = self.board.pending_promotion
                    prom_tile = self.board.get_tile(pq, pr)
                    if prom_tile:
                        prom_tile.piece = (pcolor, 'queen')
                    self.board.pending_promotion = None
                    self.board.current_turn = 'white' if state_snap["current_turn"] == 'black' else 'black'

                eval_score = self._minimax(depth - 1, False, alpha, beta)
                self._restore_board(pieces_snap, state_snap)

                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break # Beta cutoff
            self.transposition_table[position_key] = (depth, max_eval)
            return max_eval

        else:
            min_eval = float('inf')
            for (from_q, from_r), (to_q, to_r) in all_moves:
                pieces_snap, state_snap = self._snapshot_board()
                self.board.move_piece(from_q, from_r, to_q, to_r)
                
                if getattr(self.board, "pending_promotion", None):
                    pq, pr, pcolor = self.board.pending_promotion
                    prom_tile = self.board.get_tile(pq, pr)
                    if prom_tile:
                        prom_tile.piece = (pcolor, 'queen')
                    self.board.pending_promotion = None
                    self.board.current_turn = 'white' if state_snap["current_turn"] == 'black' else 'black'

                eval_score = self._minimax(depth - 1, True, alpha, beta)
                self._restore_board(pieces_snap, state_snap)

                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break # alpha cutoff
            self.transposition_table[position_key] = (depth, min_eval)
            return min_eval

    def find_best_move(self) -> Optional[Tuple[Tuple[int,int], Tuple[int,int], float]]:
        """Search using minimax to find best move."""
        self.nodes_searched = 0
        best_move = None
        best_value = float('-inf')
        
        # Get all legal moves for engine
        all_moves = []
        for (q, r), tile in self.board.tiles.items():
            if not tile or not tile.has_piece():
                continue
            piece_color, _ = tile.get_piece()
            if piece_color != self.engine_color:
                continue
            
            moves = self.validator.get_legal_moves_with_check(q, r)
            for (to_q, to_r) in moves:
                all_moves.append(((q, r), (to_q, to_r)))
        
        # Order moves before searching
        all_moves = self._order_moves(all_moves, self.engine_color)
        
        for (from_q, from_r), (to_q, to_r) in all_moves:
            pieces_snap, state_snap = self._snapshot_board()
            self.board.move_piece(from_q, from_r, to_q, to_r)
            
            if getattr(self.board, "pending_promotion", None):
                pq, pr, pcolor = self.board.pending_promotion
                prom_tile = self.board.get_tile(pq, pr)
                if prom_tile:
                    prom_tile.piece = (pcolor, 'queen')
                self.board.pending_promotion = None
                self.board.current_turn = 'white' if state_snap["current_turn"] == 'black' else 'black'
            
            value = self._minimax(self.search_depth - 1, False)
            self._restore_board(pieces_snap, state_snap)
            
            if value > best_value:
                best_value = value
                best_move = ((from_q, from_r), (to_q, to_r), value)
        
        print(f"Searched {self.nodes_searched} nodes.")
        return best_move

    def play_best_move(self) -> Optional[dict]:
        """
        Find best move and execute it on the real board.
        Returns a dict with move info and evaluation or None if no move possible.
        """
        best = self.find_best_move()
        if not best:
            # no legal move found (game over or nothing to do)
            return None

        (from_q, from_r), (to_q, to_r), est_value = best

        # perform the chosen move on the real board
        success = self.board.move_piece(from_q, from_r, to_q, to_r)
        if not success:
            # move unexpectedly failed; return None
            return None

        # if pending promotion was set (move_piece doesn't finalize), auto-promote to queen
        if getattr(self.board, "pending_promotion", None):
            pq, pr, pcolor = self.board.pending_promotion
            prom_tile = self.board.get_tile(pq, pr)
            if prom_tile:
                prom_tile.piece = (pcolor, 'queen')
            # clear pending_promotion and switch turn (mirror of your move_piece behavior)
            self.board.pending_promotion = None
            self.board.current_turn = 'white' if self.board.current_turn == 'black' else 'black'

        # return summary information
        final_score, total_mat, phase = Evaluator.evaluate(self.board)
        return {
            "from": (from_q, from_r),
            "to": (to_q, to_r),
            "estimated_value": est_value,
            "final_eval_score": final_score,
            "total_material": total_mat,
            "phase": phase,
            "success": True
        }
