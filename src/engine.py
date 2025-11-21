"""
Enhanced Chess Engine for Hexagonal Chess
Implements Stages 1-3 of the evaluation roadmap:
- Material evaluation with piece-square tables
- Tapered evaluation (midgame/endgame blending)
- Basic pawn structure analysis
"""

class ChessEngine:
    """Simple evaluation for material balance.

    evaluate(board) -> (score, total_material)
    - score: signed centipawn score (positive means white advantage)
    - total_material: sum of absolute piece values present on the board

    The evaluation is a simple sum of piece values; kings use a very large
    value to reflect their importance.
    """

    # Basic piece values (centipawns)
    PIECE_VALUES = {
        'pawn': 100,
        'knight': 320,
        'bishop': 330,
        'rook': 500,
        'queen': 900,
        'king': 20000  # Effectively infinite
    }

    # Piece-Square Tables for Hexagonal Board
    # These encourage good piece placement
    # Format: {(q, r): bonus} for white pieces (flip for black)
    
    # Pawn PST - encourages center control and advancement
    PAWN_PST = {
        # Starting rank (minimal bonus)
        (-4, 5): 0, (-3, 4): 0, (-2, 3): 0, (-1, 2): 0, (0, 1): 0,
        (1, 1): 0, (2, 1): 0, (3, 1): 0, (4, 1): 0,
        
        # Second rank
        (-4, 4): 5, (-3, 3): 5, (-2, 2): 5, (-1, 1): 5, (0, 0): 10,
        (1, 0): 10, (2, 0): 5, (3, 0): 5, (4, 0): 5,
        
        # Third rank (center control important)
        (-3, 2): 10, (-2, 1): 15, (-1, 0): 20, (0, -1): 25,
        (1, -1): 20, (2, -1): 15, (3, -1): 10,
        
        # Fourth rank (advanced pawns)
        (-2, 0): 20, (-1, -1): 30, (0, -2): 35, (1, -2): 30, (2, -2): 20,
        
        # Fifth rank (near promotion)
        (-1, -2): 40, (0, -3): 50, (1, -3): 40,
        
        # Sixth rank (very advanced)
        (0, -4): 60, (1, -4): 60,
    }
    
    # Knight PST - prefers center, avoids edges
    KNIGHT_PST = {
        # Center hexes (strong positions)
        (0, 0): 30, (1, -1): 25, (-1, 1): 25, (0, 1): 20, (1, 0): 20,
        (0, -1): 20, (-1, 0): 20,
        
        # Near center
        (1, 1): 15, (2, -1): 15, (2, -2): 10, (-1, 2): 15, (-2, 2): 10,
        (1, -2): 15, (-1, -1): 10, (-2, 1): 10,
        
        # Edge positions (penalty)
        (3, 2): -10, (4, 1): -20, (-3, 5): -20, (-4, 5): -30,
        (3, -5): -20, (4, -5): -30, (-3, -2): -10,
    }
    
    # Bishop PST - encourages long diagonals
    BISHOP_PST = {
        # Center control
        (0, 0): 20, (1, -1): 15, (-1, 1): 15,
        (0, 1): 10, (1, 0): 10, (0, -1): 10, (-1, 0): 10,
        
        # Good diagonal positions
        (2, -2): 15, (-2, 2): 15, (1, 1): 10, (-1, -1): 10,
        
        # Edge penalties
        (4, 1): -10, (-4, 5): -10, (4, -5): -10, (-4, -1): -10,
    }
    
    # Rook PST - prefers open files and 7th rank
    ROOK_PST = {
        # Back rank
        (3, 2): 0, (-3, 5): 0,
        
        # Advanced positions
        (0, -1): 10, (1, -1): 10, (-1, -1): 10,
        (0, -2): 15, (1, -2): 15, (-1, -2): 15,
        
        # Seventh rank equivalent (strong)
        (0, -3): 20, (1, -3): 20, (-1, -3): 20,
        (0, -4): 25, (1, -4): 25,
    }
    
    # Queen PST - slight center preference, but flexible
    QUEEN_PST = {
        (0, 0): 10, (1, -1): 10, (-1, 1): 10,
        (0, 1): 5, (1, 0): 5, (0, -1): 5, (-1, 0): 5,
        # Early development penalty
        (-1, 5): -20,  # Starting square
    }
    
    # King PST - different for middlegame vs endgame
    KING_PST_MG = {
        # Safety on back rank
        (1, 4): 20, (0, 4): 15, (2, 3): 10,
        
        # Center exposure penalty
        (0, 0): -40, (1, -1): -30, (-1, 1): -30,
        (0, 1): -20, (1, 0): -20, (0, -1): -20, (-1, 0): -20,
    }
    
    KING_PST_EG = {
        # Center is good in endgame
        (0, 0): 30, (1, -1): 25, (-1, 1): 25,
        (0, 1): 20, (1, 0): 20, (0, -1): 20, (-1, 0): 20,
        
        # Back rank less important
        (1, 4): 0, (0, 4): 0, (2, 3): 5,
    }

    @staticmethod
    def get_pst_bonus(piece_name, q, r, color, phase):
        """
        Get piece-square table bonus for a piece.
        
        Args:
            piece_name: Type of piece
            q, r: Axial coordinates
            color: 'white' or 'black'
            phase: Game phase (0.0 = endgame, 1.0 = opening)
        
        Returns:
            Bonus in centipawns
        """
        # Get the appropriate PST
        if piece_name == 'pawn':
            pst = ChessEngine.PAWN_PST
        elif piece_name == 'knight':
            pst = ChessEngine.KNIGHT_PST
        elif piece_name == 'bishop':
            pst = ChessEngine.BISHOP_PST
        elif piece_name == 'rook':
            pst = ChessEngine.ROOK_PST
        elif piece_name == 'queen':
            pst = ChessEngine.QUEEN_PST
        elif piece_name == 'king':
            # Interpolate between middlegame and endgame king tables
            mg_bonus = ChessEngine.KING_PST_MG.get((q, r), 0)
            eg_bonus = ChessEngine.KING_PST_EG.get((q, r), 0)
            bonus = phase * mg_bonus + (1 - phase) * eg_bonus
            return bonus if color == 'white' else -bonus
        else:
            return 0
        
        # For black, flip the board coordinates
        if color == 'black':
            q, r = -q, -r
        
        return pst.get((q, r), 0)

    @staticmethod
    def calculate_game_phase(board):
        """
        Calculate game phase for tapered evaluation.
        
        Returns value from 0.0 (pure endgame) to 1.0 (opening/middlegame)
        
        Based on remaining material:
        - Opening: all pieces present
        - Endgame: only kings + pawns (+ maybe one minor)
        """
        # Define piece weights for phase calculation
        # Queens and rooks contribute most to "middlegame-ness"
        phase_weights = {
            'pawn': 0,
            'knight': 1,
            'bishop': 1,
            'rook': 2,
            'queen': 4,
            'king': 0
        }
        
        # Maximum phase value (starting position)
        # 2 queens * 4 + 4 rooks * 2 + 4 bishops * 1 + 4 knights * 1 = 24
        max_phase = 24
        
        current_phase = 0
        
        for tile in board.tiles.values():
            if tile and tile.has_piece():
                _, piece_name = tile.get_piece()
                current_phase += phase_weights.get(piece_name, 0)
        
        # Normalize to 0.0-1.0 range
        phase = min(1.0, current_phase / max_phase)
        
        return phase

    @staticmethod
    def evaluate_pawn_structure(board, color):
        """
        Evaluate pawn structure for a given color.
        
        Penalties for:
        - Isolated pawns (no friendly pawns on adjacent files)
        - Doubled pawns (multiple pawns on same file)
        
        Bonuses for:
        - Passed pawns (no enemy pawns blocking or attacking)
        - Connected pawns (defended by other pawns)
        """
        score = 0
        pawn_positions = []
        
        # Collect all pawns of this color
        for (q, r), tile in board.tiles.items():
            if tile.has_piece():
                piece_color, piece_name = tile.get_piece()
                if piece_color == color and piece_name == 'pawn':
                    pawn_positions.append((q, r))
        
        # Check each pawn for structure issues
        for q, r in pawn_positions:
            # Check for doubled pawns (same q-coordinate)
            same_file = [p for p in pawn_positions if p[0] == q and p != (q, r)]
            if same_file:
                score -= 15  # Penalty for doubled pawn
            
            # Check for isolated pawns (no friendly pawns on adjacent files)
            adjacent_files = [q-1, q+1]
            has_neighbor = any(
                p[0] in adjacent_files 
                for p in pawn_positions 
                if p != (q, r)
            )
            if not has_neighbor:
                score -= 10  # Penalty for isolated pawn
            
            # Check for passed pawns (basic check)
            is_passed = ChessEngine._is_passed_pawn(board, q, r, color)
            if is_passed:
                # Bonus increases with advancement
                if color == 'white':
                    advancement = (5 - r)  # Lower r = more advanced for white
                else:
                    advancement = (r + 5)  # Higher r = more advanced for black
                score += 20 + (advancement * 5)
        
        return score

    @staticmethod
    def _is_passed_pawn(board, q, r, color):
        """Check if a pawn is passed (no enemy pawns in front)."""
        enemy_color = 'black' if color == 'white' else 'white'
        
        # Define "in front" based on color
        if color == 'white':
            # White pawns move toward negative r
            check_r_range = range(r - 1, -6, -1)
        else:
            # Black pawns move toward positive r
            check_r_range = range(r + 1, 6)
        
        # Check file and adjacent files
        for check_q in [q - 1, q, q + 1]:
            for check_r in check_r_range:
                tile = board.get_tile(check_q, check_r)
                if tile and tile.has_piece():
                    piece_color, piece_name = tile.get_piece()
                    if piece_color == enemy_color and piece_name == 'pawn':
                        return False
        
        return True

    @staticmethod
    def evaluate(board):
        """
        Main evaluation function with stages 1-3 implemented.
        
        Returns: (score, total_material)
            score: Centipawn evaluation (positive = white advantage)
            total_material: Total material on board for phase calculation
        """
        score = 0
        total_material = 0
        
        # Calculate game phase
        phase = ChessEngine.calculate_game_phase(board)
        
        # Stage 1: Material + PSTs
        for (q, r), tile in board.tiles.items():
            if tile and tile.has_piece():
                color, piece_name = tile.get_piece()
                
                # Material value
                value = ChessEngine.PIECE_VALUES.get(piece_name, 0)
                total_material += abs(value) if piece_name != 'king' else 0
                
                # PST bonus
                pst_bonus = ChessEngine.get_pst_bonus(piece_name, q, r, color, phase)
                
                # Combine material + PST
                piece_score = value + pst_bonus
                
                if color == 'white':
                    score += piece_score
                else:
                    score -= piece_score
        
        # Stage 3: Pawn structure evaluation
        white_pawn_score = ChessEngine.evaluate_pawn_structure(board, 'white')
        black_pawn_score = ChessEngine.evaluate_pawn_structure(board, 'black')
        score += (white_pawn_score - black_pawn_score)
        
        # Small bonus for side to move (tempo)
        if board.current_turn == 'white':
            score += 10
        else:
            score -= 10
        
        return score, total_material