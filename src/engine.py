import copy
from typing import Optional, Tuple
from game import MoveValidator
from evaluation import Evaluator

class ChessEngine:
    """
    Simple 1-ply engine for your hex chess:
      - engine_color determined by board.flipped (True -> white, else black)
      - searches all legal moves for engine pieces (uses MoveValidator)
      - simulates each move, evaluates resulting board with Evaluator
      - chooses best move from engine's perspective and executes it (with promotion handling)
    """

    def __init__(self, board, depth=2):
        self.board = board
        # engine is white if board is flipped, otherwise black (as you specified)
        self.engine_color = 'white' if getattr(board, "flipped", False) else 'black'
        self.validator = MoveValidator(board)
        self.search_depth = depth  # Add configurable search depth

    # -------------------------
    # Snapshot / restore helpers
    # -------------------------
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

    # -------------------------
    # Move evaluation helpers
    # -------------------------
    def _evaluate_board_from_engine_perspective(self) -> float:
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

    # -------------------------
    # Main move search + play
    # -------------------------
    def _minimax(self, depth: int, is_maximizing: bool, alpha: float = float('-inf'), beta: float = float('inf')) -> float:
        """
        Minimax with alpha-beta pruning.
        is_maximizing: True if we're maximizing (engine's turn), False if minimizing (opponent's turn)
        Returns the best evaluation score from current position.
        """
        # Base case: reached max depth or game over
        if depth == 0:
            return self._evaluate_board_from_engine_perspective()

        # Check if current player has any legal moves
        has_moves = False
        for (q, r), tile in self.board.tiles.items():
            if not tile or not tile.has_piece():
                continue
            piece_color, _ = tile.get_piece()
            current_turn = getattr(self.board, "current_turn", 'white')
            if piece_color != current_turn:
                continue
            moves = self.validator.get_legal_moves_with_check(q, r)
            if moves:
                has_moves = True
                break

        # If no moves available, return current evaluation (checkmate/stalemate)
        if not has_moves:
            return self._evaluate_board_from_engine_perspective()

        if is_maximizing:
            max_eval = float('-inf')
            for (q, r), tile in self.board.tiles.items():
                if not tile or not tile.has_piece():
                    continue
                piece_color, _ = tile.get_piece()
                if piece_color != self.engine_color:
                    continue

                moves = self.validator.get_legal_moves_with_check(q, r)
                for (to_q, to_r) in moves:
                    pieces_snap, state_snap = self._snapshot_board()
                    self.board.move_piece(q, r, to_q, to_r)
                    
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
                        break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            opponent_color = 'black' if self.engine_color == 'white' else 'white'
            for (q, r), tile in self.board.tiles.items():
                if not tile or not tile.has_piece():
                    continue
                piece_color, _ = tile.get_piece()
                if piece_color != opponent_color:
                    continue

                moves = self.validator.get_legal_moves_with_check(q, r)
                for (to_q, to_r) in moves:
                    pieces_snap, state_snap = self._snapshot_board()
                    self.board.move_piece(q, r, to_q, to_r)
                    
                    # Handle promotion
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
                        break  # Alpha cutoff
            return min_eval

    def find_best_move(self) -> Optional[Tuple[Tuple[int,int], Tuple[int,int], float]]:
        """
        Search using minimax to find best move considering multiple plies ahead.
        """
        best_move = None
        best_value = float('-inf')

        for (q, r), tile in self.board.tiles.items():
            if not tile or not tile.has_piece():
                continue
            piece_color, _ = tile.get_piece()
            if piece_color != self.engine_color:
                continue

            moves = self.validator.get_legal_moves_with_check(q, r)
            for (to_q, to_r) in moves:
                pieces_snap, state_snap = self._snapshot_board()
                self.board.move_piece(q, r, to_q, to_r)
                
                # Handle promotion
                if getattr(self.board, "pending_promotion", None):
                    pq, pr, pcolor = self.board.pending_promotion
                    prom_tile = self.board.get_tile(pq, pr)
                    if prom_tile:
                        prom_tile.piece = (pcolor, 'queen')
                    self.board.pending_promotion = None
                    self.board.current_turn = 'white' if state_snap["current_turn"] == 'black' else 'black'

                # Evaluate with minimax from opponent's perspective
                value = self._minimax(self.search_depth - 1, False)
                self._restore_board(pieces_snap, state_snap)

                if value > best_value:
                    best_value = value
                    best_move = ((q, r), (to_q, to_r), value)

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
