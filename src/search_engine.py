"""
Fixed Chess Search Engine
- Auto-promotes pawns during AI moves (always to Queen)
- Fixed evaluation consistency
- Better move ordering
"""

import copy
import time
from typing import Tuple, Optional, List

class SearchEngine:
    """
    Implements minimax search with alpha-beta pruning.
    Fixed to handle pawn promotion automatically.
    """
    
    def __init__(self, evaluator, move_validator):
        """
        Args:
            evaluator: ChessEngine class with evaluate() method
            move_validator: MoveValidator to get legal moves and check game state
        """
        self.evaluator = evaluator
        self.move_validator = move_validator
        self.nodes_searched = 0
        self.best_move_this_iteration = None
        
    def find_best_move(self, board, depth=3, max_time=5.0):
        """
        Find the best move for the current player.
        
        Args:
            board: HexBoard instance
            depth: How many moves ahead to search (3 = you, opponent, you)
            max_time: Maximum seconds to think
            
        Returns:
            ((from_q, from_r), (to_q, to_r)) or None if no legal moves
        """
        self.nodes_searched = 0
        start_time = time.time()
        
        color = board.current_turn
        legal_moves = self._get_all_legal_moves(board, color)
        
        if not legal_moves:
            return None  # No legal moves (checkmate or stalemate)
        
        # Sort moves to search promising ones first (move ordering)
        legal_moves = self._order_moves(board, legal_moves)
        
        best_move = None
        best_score = float('-inf') if color == 'white' else float('inf')
        
        # Iterative deepening - search depth 1, 2, 3... until time runs out
        for current_depth in range(1, depth + 1):
            if time.time() - start_time > max_time:
                break
                
            for move in legal_moves:
                if time.time() - start_time > max_time:
                    break
                    
                from_pos, to_pos = move
                
                # Make move on a copy of the board
                board_copy = copy.deepcopy(board)
                self._make_move_with_auto_promotion(board_copy, from_pos[0], from_pos[1], 
                                                     to_pos[0], to_pos[1])
                
                # Search this position
                score = self._minimax(
                    board_copy,
                    current_depth - 1,
                    float('-inf'),
                    float('inf'),
                    board_copy.current_turn == 'white'
                )
                
                # Update best move if this is better
                if color == 'white':
                    if score > best_score:
                        best_score = score
                        best_move = move
                        self.best_move_this_iteration = move
                else:
                    if score < best_score:
                        best_score = score
                        best_move = move
                        self.best_move_this_iteration = move
            
            print(f"Depth {current_depth}: Best move {best_move}, Score {best_score:.1f}, Nodes {self.nodes_searched}")
        
        elapsed = time.time() - start_time
        print(f"Search completed in {elapsed:.2f}s, {self.nodes_searched} nodes, {self.nodes_searched/elapsed:.0f} nodes/sec")
        
        return best_move
    
    def _make_move_with_auto_promotion(self, board, from_q, from_r, to_q, to_r):
        """
        Make a move and automatically promote pawns to Queen.
        This prevents the AI from getting stuck waiting for promotion input.
        """
        # Make the move
        board.move_piece(from_q, from_r, to_q, to_r)
        
        # If there's a pending promotion, automatically promote to Queen
        if board.pending_promotion:
            board.promote_pawn('queen')
    
    def _minimax(self, board, depth, alpha, beta, maximizing):
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            board: Current position
            depth: Moves remaining to search
            alpha: Best score for maximizer (white)
            beta: Best score for minimizer (black)
            maximizing: True if white's turn
            
        Returns:
            Best score found from this position
        """
        self.nodes_searched += 1
        
        # Terminal conditions
        if depth == 0:
            # Use only the score, ignore total material
            score, _ = self.evaluator.evaluate(board)
            return score
        
        # Update move validator to use current board
        self.move_validator.board = board
        self.move_validator.move_generator.board = board
        
        # Check for game over
        game_status = self.move_validator.get_game_status()
        if game_status == 'checkmate':
            # Mate is very bad for current player
            # Prefer faster mates (shorter depth to mate)
            mate_score = 20000 - (10 - depth)
            return -mate_score if maximizing else mate_score
        elif game_status in ['stalemate', 'draw']:
            return 0
        
        color = 'white' if maximizing else 'black'
        legal_moves = self._get_all_legal_moves(board, color)
        
        if not legal_moves:
            return 0  # Stalemate
        
        # Order moves for better pruning
        legal_moves = self._order_moves(board, legal_moves)
        
        if maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                from_pos, to_pos = move
                
                # Make move
                board_copy = copy.deepcopy(board)
                self._make_move_with_auto_promotion(board_copy, from_pos[0], from_pos[1], 
                                                     to_pos[0], to_pos[1])
                
                # Recursive search
                eval_score = self._minimax(board_copy, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                
                # Alpha-beta pruning
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
                    
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                from_pos, to_pos = move
                
                # Make move
                board_copy = copy.deepcopy(board)
                self._make_move_with_auto_promotion(board_copy, from_pos[0], from_pos[1], 
                                                     to_pos[0], to_pos[1])
                
                # Recursive search
                eval_score = self._minimax(board_copy, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                
                # Alpha-beta pruning
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
                    
            return min_eval
    
    def _get_all_legal_moves(self, board, color):
        """
        Get all legal moves for a color.
        CRITICAL: Must create new MoveValidator for the board being evaluated!
        
        Returns:
            List of ((from_q, from_r), (to_q, to_r)) tuples
        """
        from game import MoveValidator, MoveGenerator
        
        # Create a fresh MoveValidator for this specific board
        validator = MoveValidator(board)
        
        moves = []
        
        for (q, r), tile in board.tiles.items():
            if not tile.has_piece():
                continue
                
            piece_color, _ = tile.get_piece()
            if piece_color != color:
                continue
            
            # Get legal moves for this piece using the correct validator
            piece_moves = validator.get_legal_moves_with_check(q, r)
            
            for to_q, to_r in piece_moves:
                moves.append(((q, r), (to_q, to_r)))
        
        return moves
    
    def _order_moves(self, board, moves):
        """
        Order moves to search promising ones first.
        This improves alpha-beta pruning efficiency.
        
        Move ordering heuristics:
        1. Captures (especially capturing valuable pieces)
        2. Checks
        3. Promotions
        4. Center control
        5. Other moves
        """
        def move_score(move):
            from_pos, to_pos = move
            score = 0
            
            from_tile = board.get_tile(*from_pos)
            to_tile = board.get_tile(*to_pos)
            
            if not from_tile or not to_tile:
                return 0
            
            piece_color, piece_name = from_tile.get_piece()
            
            # Capture bonus (MVV-LVA: Most Valuable Victim, Least Valuable Attacker)
            if to_tile.has_piece():
                _, victim_piece = to_tile.get_piece()
                
                victim_value = self.evaluator.PIECE_VALUES.get(victim_piece, 0)
                attacker_value = self.evaluator.PIECE_VALUES.get(piece_name, 0)
                
                # Capturing high-value pieces is good
                # Using low-value attackers is better
                score += 10000 + (victim_value * 10 - attacker_value)
            
            # Pawn promotion bonus (very high priority)
            if piece_name == 'pawn':
                if board.is_promotion_square(to_pos[0], to_pos[1], piece_color):
                    score += 9000  # Almost as good as capturing queen
            
            # Center control bonus
            center_hexes = [(0, 0), (1, -1), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, 0)]
            if to_pos in center_hexes:
                score += 50
            
            # Avoid moving to attacked squares (basic)
            # This would require another function, skip for now
            
            return score
        
        # Sort moves by score (highest first)
        return sorted(moves, key=move_score, reverse=True)