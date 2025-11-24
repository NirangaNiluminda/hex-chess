from constants import PIECE_VALUES, MAX_PHASE, PHASE_VALUES, BOARD_SIZE
from hex_board import HexGeometry

class ProceduralPST:
    """Procedural piece-square table generation for hexagonal boards."""
        
    @staticmethod
    def pawn_pst(q: int, r: int, color: str, is_endgame: bool = False) -> int:
        """
        Pawn evaluation based on advancement toward center/promotion.
        Returns starting_penalty + advancement_bonus + centrality_bonus
        """
        center_dist = HexGeometry.distance_from_center(q, r)
        edge_dist = HexGeometry.distance_from_edge(q, r, BOARD_SIZE)
        file_centrality = HexGeometry.get_file_centrality(q, BOARD_SIZE)
        
        # Base advancement bonus - pawns closer to center are more advanced
        # At edge_dist=0 (edge), pawns are on back rank. At edge_dist=5, closer to promotion
        advancement_bonus = edge_dist * 10
        
        if is_endgame:
            # Endgame: pawns much more valuable, especially advanced ones
            advancement_bonus = edge_dist * 20
            # Massive bonus for pawns deep in opponent territory
            if edge_dist >= 4:
                advancement_bonus += (edge_dist - 3) * 80
        else:
            # Middlegame: moderate bonus for advancement
            if edge_dist >= 4:
                advancement_bonus += (edge_dist - 3) * 25
        
        # Central files are better
        centrality_bonus = file_centrality * 3
        
        # Starting position penalty (don't sit on edge/back rank)
        starting_penalty = -20 if edge_dist == 0 else 0
        
        return starting_penalty + advancement_bonus + centrality_bonus

    @staticmethod
    def knight_pst(q: int, r: int, color: str, is_endgame: bool = False) -> int:
        """
        Knight evaluation based on centralization.
        """
        center_dist = HexGeometry.distance_from_center(q, r)
        edge_dist = HexGeometry.distance_from_edge(q, r, BOARD_SIZE)
        
        # Knights want to be central
        centralization_bonus = edge_dist * 15
        center_penalty = center_dist * -8
        
        # Edge penalty (knights on rim are dim)
        if edge_dist == 0:
            edge_penalty = -40
        elif edge_dist == 1:
            edge_penalty = -15
        else:
            edge_penalty = 0
        
        # Knights slightly worse in endgame
        endgame_penalty = -10 if is_endgame else 0
        
        return centralization_bonus + center_penalty + edge_penalty + endgame_penalty
    
    @staticmethod
    def bishop_pst(q: int, r: int, color: str, is_endgame: bool = False) -> int:
        """
        Bishop evaluation based on long diagonal control.
        Color-independent (centralization is same for both).
        """
        center_dist = HexGeometry.distance_from_center(q, r)
        edge_dist = HexGeometry.distance_from_edge(q, r, BOARD_SIZE)
        
        # Bishops want central positions for maximum diagonal control
        centralization_bonus = (4 - center_dist) * 8
        
        # Edge penalty
        edge_penalty = -20 if edge_dist == 0 else 0
        
        # Bishops better in endgame (more open board)
        endgame_bonus = 5 if is_endgame else 0
        
        return centralization_bonus + edge_penalty + endgame_bonus
    

    @staticmethod
    def rook_pst(q: int, r: int, color: str, is_endgame: bool = False) -> int:
        """
        Rook evaluation based on penetration into opponent territory.
        Symmetrical for both colors.
        """
        center_dist = HexGeometry.distance_from_center(q, r)
        edge_dist = HexGeometry.distance_from_edge(q, r, BOARD_SIZE)
        file_centrality = HexGeometry.get_file_centrality(q, BOARD_SIZE)
        
        # Base value for all positions
        base = 5
        
        # Reward penetration (rooks deep in opponent territory are powerful)
        if edge_dist >= 4:
            advancement_bonus = 35
        elif edge_dist >= 3:
            advancement_bonus = 20
        elif edge_dist >= 2:
            advancement_bonus = 10
        else:
            advancement_bonus = 0
        
        # Slight preference for central files
        centrality_bonus = file_centrality * 2
        
        # In endgame, rooks are active everywhere
        if is_endgame:
            endgame_bonus = 10
            # Less emphasis on advancement in endgame
            advancement_bonus = advancement_bonus // 2
        else:
            endgame_bonus = 0
        
        return base + advancement_bonus + centrality_bonus + endgame_bonus

    @staticmethod
    def queen_pst(q: int, r: int, color: str, is_endgame: bool = False) -> int:
        """
        Queen evaluation based on centralization.
        Color-independent (centralization is same for both).
        """
        center_dist = HexGeometry.distance_from_center(q, r)
        edge_dist = HexGeometry.distance_from_edge(q, r, BOARD_SIZE)
        
        # Mild central preference
        centralization_bonus = (4 - center_dist) * 5
        
        # Edge penalty in middlegame (queen too exposed)
        if not is_endgame:
            if edge_dist == 0:
                edge_penalty = -20
            elif edge_dist == 1:
                edge_penalty = -10
            else:
                edge_penalty = 0
        else:
            edge_penalty = 0
        
        # More active in endgame
        endgame_bonus = 10 if is_endgame else 0
        
        return centralization_bonus + edge_penalty + endgame_bonus
    
    # @staticmethod
    # def king_pst(q: int, r: int, color: str, is_endgame: bool = False) -> int:
    #     """
    #     King evaluation - complete opposite in middlegame vs endgame.
    #     Symmetrical for both colors.
    #     """
    #     rank = HexGeometry.get_rank(q, r, color, BOARD_SIZE)
    #     center_dist = HexGeometry.distance_from_center(q, r)
    #     edge_dist = HexGeometry.distance_from_edge(q, r, BOARD_SIZE)
    #     file_centrality = HexGeometry.get_file_centrality(q, BOARD_SIZE)
        
    #     if is_endgame:
    #         # ENDGAME: King should be centralized and active
    #         centralization_bonus = (4 - center_dist) * 10
            
    #         # Back rank is bad in endgame
    #         if rank <= 1:
    #             back_rank_penalty = -40
    #         elif rank <= 2:
    #             back_rank_penalty = -20
    #         else:
    #             back_rank_penalty = 0
            
    #         return centralization_bonus + back_rank_penalty
    #     else:
    #         # MIDDLEGAME: King should be safe on back ranks
    #         # Prefer back rank positions (rank 0-1)
    #         if rank <= 1:
    #             safety_bonus = 50  # Strong bonus for being on/near back rank
    #         elif rank == 2:
    #             safety_bonus = 10
    #         else:
    #             safety_bonus = 0
            
    #         # Prefer edges in middlegame (castled position)
    #         if edge_dist <= 1 and file_centrality <= 1:
    #             edge_bonus = 20
    #         else:
    #             edge_bonus = 0
            
    #         # Center is dangerous (distance from center is good)
    #         center_safety = center_dist * 15
            
    #         # Forward movement is dangerous
    #         if rank >= 3:
    #             exposure_penalty = -30
    #         elif rank == 2:
    #             exposure_penalty = -15
    #         else:
    #             exposure_penalty = 0
            
    #         return safety_bonus + edge_bonus + center_safety + exposure_penalty

    @staticmethod
    def king_pst(q: int, r: int, color: str, is_endgame: bool = False) -> int:
        """
        King evaluation - complete opposite in middlegame vs endgame.
        Symmetrical for both colors.
        """
        center_dist = HexGeometry.distance_from_center(q, r)
        edge_dist = HexGeometry.distance_from_edge(q, r, BOARD_SIZE)
        file_centrality = HexGeometry.get_file_centrality(q, BOARD_SIZE)
        
        if is_endgame:
            # ENDGAME: King should be centralized and active
            centralization_bonus = (4 - center_dist) * 10
            return centralization_bonus
        else:
            # MIDDLEGAME: King should be safe - use edge_dist instead of rank
            # Prefer edges (distance from center but on the perimeter)
            if edge_dist <= 1:
                safety_bonus = 50  # Safe on edge
            elif edge_dist == 2:
                safety_bonus = 20
            else:
                safety_bonus = -30  # Dangerous in center
            
            # Avoid absolute center
            center_penalty = center_dist * -5
            
            return safety_bonus + center_penalty
        

class PST:
    """Piece-Square Tables using procedural generation."""
    
    @staticmethod
    def get_pst_value(piece_name: str, q: int, r: int, color: str, phase: int) -> int:
        """
        Get procedurally generated PST value.
        
        Args:
            piece_name: Name of the piece
            q, r: Axial coordinates
            color: 'white' or 'black'
            phase: Current game phase (0 to MAX_PHASE)
            
        Returns:
            Centipawn value for this piece's position
        """
        MAX_PHASE = 26
        
        # Map piece names to their PST functions
        piece_funcs = {
            'pawn': ProceduralPST.pawn_pst,
            'knight': ProceduralPST.knight_pst,
            'bishop': ProceduralPST.bishop_pst,
            'rook': ProceduralPST.rook_pst,
            'queen': ProceduralPST.queen_pst,
            'king': ProceduralPST.king_pst,
        }
        
        func = piece_funcs.get(piece_name)
        if not func:
            return 0
        
        # Calculate both MG and EG values using actual coordinates and color
        mg_value = func(q, r, color, is_endgame=False)
        eg_value = func(q, r, color, is_endgame=True)
        
        # Tapered evaluation: blend MG and EG based on phase
        tapered_value = (mg_value * phase + eg_value * (MAX_PHASE - phase)) // MAX_PHASE
        
        return tapered_value


class Evaluator:
    """Evaluation calculation based on material balance and positional advantage."""
    
    @staticmethod
    def calculate_phase(board) -> int:
        """Calculate the current game phase based on remaining material."""
        phase = 0
        
        for tile in board.tiles.values():
            if tile and tile.has_piece():
                color, name = tile.get_piece()
                phase += PHASE_VALUES.get(name, 0)
        
        # Clamp phase to MAX_PHASE
        return min(phase, MAX_PHASE)
    
    @staticmethod
    def evaluate(board):
        """
        Evaluate the board position.
        
        Returns:
            Tuple of (score, total_material, phase)
            - score: positive favors white, negative favors black
            - total_material: sum of all piece values on board
            - phase: current game phase
        """
        score = 0
        total_material = 0
        
        # Calculate game phase first
        phase = Evaluator.calculate_phase(board)
        
        # Iterate over all tiles
        for tile in board.tiles.values():
            if tile and tile.has_piece():
                color, name = tile.get_piece()
                q, r = tile.q, tile.r
                
                # Material value
                material_value = PIECE_VALUES.get(name, 0)
                if name != 'king': # don't count kings in total material
                    total_material += material_value
          
                # Positional value from PST
                pst_value = PST.get_pst_value(name, q, r, color, phase)
                
                # Total piece value (material + position)
                piece_value = material_value + pst_value
                
                # Add to score (positive for white, negative for black)
                if color == 'white':
                    score += piece_value
                else:
                    score -= piece_value
        
        return score, total_material, phase
    
    @staticmethod
    def debug_position(board):
        """
        Debug helper to show all pieces and their evaluations.
        Verifies symmetry in starting position.
        """
        phase = Evaluator.calculate_phase(board)
        
        print("\n=== POSITION DEBUG ===")
        print(f"Phase: {phase}/{MAX_PHASE}\n")
        
        white_pieces = []
        black_pieces = []
        
        for tile in board.tiles.values():
            if tile and tile.has_piece():
                color, name = tile.get_piece()
                q, r = tile.q, tile.r
                mat_val = PIECE_VALUES.get(name, 0)
                pst_val = PST.get_pst_value(name, q, r, color, phase)
                
                # Get rank and geometric properties for debugging
                rank = HexGeometry.get_rank(q, r, color, 5)
                center_dist = HexGeometry.distance_from_center(q, r)
                edge_dist = HexGeometry.distance_from_edge(q, r, 5)
                
                piece_info = {
                    'pos': (q, r),
                    'name': name,
                    'material': mat_val,
                    'pst': pst_val,
                    'total': mat_val + pst_val,
                    'rank': rank,
                    'center_dist': center_dist,
                    'edge_dist': edge_dist
                }
                
                if color == 'white':
                    white_pieces.append(piece_info)
                else:
                    black_pieces.append(piece_info)
        
        print("WHITE PIECES:")
        white_total = 0
        for p in sorted(white_pieces, key=lambda x: x['pos']):
            print(f"  {p['name']:6} at ({p['pos'][0]:2},{p['pos'][1]:2}) "
                  f"rank={p['rank']} center={p['center_dist']} edge={p['edge_dist']}: "
                  f"mat={p['material']:4} pst={p['pst']:+4} total={p['total']:4}")
            white_total += p['total']
        
        print(f"\nWhite total: {white_total}")
        
        print("\nBLACK PIECES:")
        black_total = 0
        for p in sorted(black_pieces, key=lambda x: x['pos']):
            print(f"  {p['name']:6} at ({p['pos'][0]:2},{p['pos'][1]:2}) "
                  f"rank={p['rank']} center={p['center_dist']} edge={p['edge_dist']}: "
                  f"mat={p['material']:4} pst={p['pst']:+4} total={p['total']:4}")
            black_total += p['total']
        
        print(f"\nBlack total: {black_total}")
        print(f"\nNet evaluation (white - black): {white_total - black_total}")
        
        # Check for asymmetries
        print("\n=== CHECKING SYMMETRY ===")
        white_by_type = {}
        black_by_type = {}
        
        for p in white_pieces:
            white_by_type[p['name']] = white_by_type.get(p['name'], 0) + 1
        for p in black_pieces:
            black_by_type[p['name']] = black_by_type.get(p['name'], 0) + 1
        
        print("Piece counts:")
        all_types = set(white_by_type.keys()) | set(black_by_type.keys())
        for piece_type in sorted(all_types):
            w_count = white_by_type.get(piece_type, 0)
            b_count = black_by_type.get(piece_type, 0)
            match = "✓" if w_count == b_count else "✗"
            print(f"  {piece_type:6}: White={w_count}, Black={b_count} {match}")
        
        # Check position symmetry for kings
        print("\n=== KING POSITION ANALYSIS ===")
        white_king = [p for p in white_pieces if p['name'] == 'king'][0]
        black_king = [p for p in black_pieces if p['name'] == 'king'][0]
        print(f"White king: pos={white_king['pos']}, rank={white_king['rank']}, "
              f"center_dist={white_king['center_dist']}, edge_dist={white_king['edge_dist']}")
        print(f"Black king: pos={black_king['pos']}, rank={black_king['rank']}, "
              f"center_dist={black_king['center_dist']}, edge_dist={black_king['edge_dist']}")
        print(f"PST difference: {white_king['pst']} - {black_king['pst']} = {white_king['pst'] - black_king['pst']}")