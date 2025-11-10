import pygame
import os
from typing import Tuple, Optional, Dict


class PieceImageManager:
    """Manages loading and caching of piece images.

    Accepts a hex_radius so images can be scaled to the board size.
    """
    
    def __init__(self, assets_folder: str = "assets", hex_radius: int = 40):
        self.assets_folder = assets_folder
        self.hex_radius = hex_radius
        self.images: Dict[Tuple[str, str], pygame.Surface] = {}
        self._load_images()
    
    def _load_images(self):
        """Load all piece images from assets folder."""
        if not os.path.exists(self.assets_folder):
            print(f"Warning: Assets folder '{self.assets_folder}' not found.")
            return
        
        # Expected piece names
        piece_names = ["king", "queen", "rook", "bishop", "knight", "pawn"]
        colors = ["white", "black"]
        
        for color in colors:
            for piece in piece_names:
                filename = f"{color}-{piece}.svg.png"
                filepath = os.path.join(self.assets_folder, filename)
                
                if os.path.exists(filepath):
                    try:
                        image = pygame.image.load(filepath)
                        # Scale image to fit hex (slightly smaller than hex radius)
                        target_size = max(8, int(self.hex_radius * 1.4))
                        image = pygame.transform.smoothscale(image, (target_size, target_size))
                        self.images[(color, piece)] = image
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
                else:
                    print(f"Warning: Image not found: {filename}")
    
    def get_image(self, color: str, piece_name: str) -> Optional[pygame.Surface]:
        """Get the image for a specific piece."""
        return self.images.get((color, piece_name))

