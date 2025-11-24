# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 900
HEX_RADIUS = 40
BOARD_SIZE = 6

# Colors
WHITE = (255, 255, 255)
BLACK = (50, 50, 50)
GREY = (170, 170, 170)
BACKGROUND = (238, 238,210)
OUTLINE = (30, 30, 30)
HIGHLIGHT = (255, 253, 208)
LEGAL_MOVE_HIGHLIGHT = (144, 238, 144, 100)

# Piece values in centipawns
PIECE_VALUES = {
    'pawn': 100,
    'knight': 320,
    'bishop': 330,
    'rook': 500,
    'queen': 900,
    'king': 20000
}

# Phase calculation
MAX_PHASE = 26  # 4*Knight + 6*Bishop + 4*Rook + 2*Queen
PHASE_VALUES = {
    'knight': 1,
    'bishop': 1,
    'rook': 2,
    'queen': 4,
    'pawn': 0,
    'king': 0
}
