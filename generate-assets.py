#!/usr/bin/env python3
"""
Generate high-quality kindergarten worksheet images locally using PIL
Store them in the repo as static assets
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

# Repo paths
REPO_ROOT = Path("/home/hari-homelab/kindergarten-tools")
ASSETS_DIR = REPO_ROOT / "public" / "assets" / "worksheets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def get_fonts():
    """Get fonts with fallback"""
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        for font_path in font_paths:
            try:
                return (
                    ImageFont.truetype(font_path, 96),
                    ImageFont.truetype(font_path, 48),
                    ImageFont.truetype(font_path, 32),
                )
            except:
                continue
    except:
        pass
    
    return (
        ImageFont.load_default(),
        ImageFont.load_default(),
        ImageFont.load_default(),
    )

def generate_letter_worksheet(letter, filename):
    """Generate letter tracing worksheet"""
    w, h = 800, 600
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    font_lg, font_md, font_sm = get_fonts()
    
    # Border
    draw.rectangle([20, 20, w-20, h-20], outline='black', width=3)
    
    # Title
    draw.text((w//2 - 80, 50), f"Letter {letter}", fill='black', font=font_md)
    
    # Large letter
    draw.text((w//2 - 50, 120), letter, fill='black', font=font_lg)
    
    # Tracing lines
    y = 300
    for i in range(3):
        draw.line([(100, y), (700, y)], fill='black', width=2)
        for x in range(120, 680, 15):
            draw.line([(x, y), (x+6, y)], fill='black', width=2)
        y += 70
    
    img.save(filename, 'JPEG', quality=90)

def generate_number_worksheet(num, filename):
    """Generate number tracing worksheet"""
    w, h = 800, 600
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    font_lg, font_md, font_sm = get_fonts()
    
    # Border
    draw.rectangle([20, 20, w-20, h-20], outline='black', width=3)
    
    # Title
    draw.text((w//2 - 100, 50), f"Number {num}", fill='black', font=font_md)
    
    # Large number
    draw.text((w//2 - 60, 120), str(num), fill='black', font=font_lg)
    
    # Tracing lines
    y = 300
    for i in range(3):
        draw.line([(100, y), (700, y)], fill='black', width=2)
        for x in range(120, 680, 15):
            draw.line([(x, y), (x+6, y)], fill='black', width=2)
        y += 70
    
    img.save(filename, 'JPEG', quality=90)

def generate_shapes_worksheet(filename):
    """Generate shapes worksheet"""
    w, h = 800, 600
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    font_lg, font_md, font_sm = get_fonts()
    
    # Border
    draw.rectangle([20, 20, w-20, h-20], outline='black', width=3)
    
    # Shapes
    shapes = [
        ('Circle', lambda: draw.ellipse([80, 100, 200, 220], outline='black', width=3)),
        ('Square', lambda: draw.rectangle([250, 100, 370, 220], outline='black', width=3)),
        ('Triangle', lambda: draw.polygon([(470, 220), (550, 100), (630, 220)], outline='black', width=3)),
        ('Rectangle', lambda: draw.rectangle([80, 300, 220, 420], outline='black', width=3)),
        ('Diamond', lambda: draw.polygon([(400, 300), (450, 250), (500, 300), (450, 350)], outline='black', width=3)),
    ]
    
    positions = [(50, 250), (200, 250), (450, 250), (50, 480), (350, 480)]
    
    for (name, draw_shape), (x, y) in zip(shapes, positions):
        draw_shape()
        draw.text((x, y), name, fill='black', font=font_sm)
    
    img.save(filename, 'JPEG', quality=90)

def generate_maze_worksheet(filename):
    """Generate simple maze"""
    w, h = 800, 600
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    font_lg, font_md, font_sm = get_fonts()
    
    # Border
    draw.rectangle([20, 20, w-20, h-20], outline='black', width=3)
    draw.rectangle([80, 80, w-80, h-120], outline='black', width=3)
    
    # Start
    draw.ellipse([100, 100, 130, 130], fill='green', outline='black', width=2)
    draw.text((140, 110), 'START', fill='black', font=font_sm)
    
    # End
    draw.ellipse([w-130, h-140, w-100, h-110], fill='red', outline='black', width=2)
    draw.text((w-130, h-95), 'END', fill='black', font=font_sm)
    
    # Maze paths
    draw.line([(150, 150), (w-150, 150)], fill='black', width=3)
    draw.line([(w-150, 150), (w-150, 300)], fill='black', width=3)
    draw.line([(200, 250), (w-200, 250)], fill='black', width=3)
    draw.line([(w-200, 250), (w-200, h-150)], fill='black', width=3)
    draw.line([(150, 300), (300, 300)], fill='black', width=3)
    draw.line([(300, 300), (300, h-150)], fill='black', width=3)
    
    draw.text((w//2 - 150, h-60), 'Find the path from START to END!', fill='black', font=font_md)
    
    img.save(filename, 'JPEG', quality=90)

def generate_colors_worksheet(filename):
    """Generate color identification worksheet"""
    w, h = 800, 600
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    font_lg, font_md, font_sm = get_fonts()
    
    # Border
    draw.rectangle([20, 20, w-20, h-20], outline='black', width=3)
    
    colors = [
        ('Red', (255, 100, 100)),
        ('Blue', (100, 150, 255)),
        ('Yellow', (255, 255, 100)),
        ('Green', (100, 200, 100)),
        ('Orange', (255, 165, 50)),
        ('Purple', (180, 100, 255)),
    ]
    
    positions = [(80, 100), (320, 100), (560, 100), (80, 360), (320, 360), (560, 360)]
    
    for (name, rgb), (x, y) in zip(colors, positions):
        draw.rectangle([x, y, x+120, y+130], fill=rgb, outline='black', width=2)
        draw.text((x+20, y+140), name, fill='black', font=font_sm)
    
    img.save(filename, 'JPEG', quality=90)

def generate_coloring_worksheet(filename):
    """Generate coloring page"""
    w, h = 800, 600
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    font_lg, font_md, font_sm = get_fonts()
    
    # Border
    draw.rectangle([20, 20, w-20, h-20], outline='black', width=3)
    
    # Happy sun
    cx, cy = w//2, 200
    draw.ellipse([cx-100, cy-100, cx+100, cy+100], outline='black', width=3)
    draw.ellipse([cx-40, cy-30, cx-20, cy-10], outline='black', width=2)
    draw.ellipse([cx+20, cy-30, cx+40, cy-10], outline='black', width=2)
    draw.arc([cx-50, cy-30, cx+50, cy+50], 0, 180, fill='black', width=3)
    
    # Rays
    for i in range(12):
        angle = i * 30 * math.pi / 180
        x1 = cx + 120 * math.cos(angle)
        y1 = cy + 120 * math.sin(angle)
        x2 = cx + 180 * math.cos(angle)
        y2 = cy + 180 * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill='black', width=3)
    
    draw.text((w//2 - 120, 350), 'Color me!', fill='black', font=font_md)
    
    img.save(filename, 'JPEG', quality=90)

def main():
    index = {}
    
    print("🎨 Generating high-quality worksheets locally...")
    
    # Letters
    index['letters'] = []
    for i in range(1, 6):
        letter = chr(64 + i)
        filename = ASSETS_DIR / 'letters' / f'letters_{i:02d}.jpg'
        filename.parent.mkdir(exist_ok=True)
        generate_letter_worksheet(letter, filename)
        index['letters'].append({
            'id': i,
            'idea': f'Letter {letter} tracing worksheet',
            'image': f'assets/worksheets/letters/letters_{i:02d}.jpg',
            'size_kb': filename.stat().st_size / 1024
        })
        print(f"✅ Letter {letter}")
    
    # Numbers
    index['numbers'] = []
    for i in range(1, 6):
        filename = ASSETS_DIR / 'numbers' / f'numbers_{i:02d}.jpg'
        filename.parent.mkdir(exist_ok=True)
        generate_number_worksheet(i, filename)
        index['numbers'].append({
            'id': i,
            'idea': f'Number {i} tracing practice',
            'image': f'assets/worksheets/numbers/numbers_{i:02d}.jpg',
            'size_kb': filename.stat().st_size / 1024
        })
        print(f"✅ Number {i}")
    
    # Shapes
    index['shapes'] = []
    filename = ASSETS_DIR / 'shapes' / 'shapes_01.jpg'
    filename.parent.mkdir(exist_ok=True)
    generate_shapes_worksheet(filename)
    index['shapes'].append({
        'id': 1,
        'idea': 'Basic shapes: circle, square, triangle, rectangle, diamond',
        'image': f'assets/worksheets/shapes/shapes_01.jpg',
        'size_kb': filename.stat().st_size / 1024
    })
    print(f"✅ Shapes")
    
    # Maze
    index['mazes'] = []
    filename = ASSETS_DIR / 'mazes' / 'mazes_01.jpg'
    filename.parent.mkdir(exist_ok=True)
    generate_maze_worksheet(filename)
    index['mazes'].append({
        'id': 1,
        'idea': 'Simple maze: find the path from START to END',
        'image': f'assets/worksheets/mazes/mazes_01.jpg',
        'size_kb': filename.stat().st_size / 1024
    })
    print(f"✅ Maze")
    
    # Colors
    index['colors'] = []
    filename = ASSETS_DIR / 'colors' / 'colors_01.jpg'
    filename.parent.mkdir(exist_ok=True)
    generate_colors_worksheet(filename)
    index['colors'].append({
        'id': 1,
        'idea': 'Color recognition: red, blue, yellow, green, orange, purple',
        'image': f'assets/worksheets/colors/colors_01.jpg',
        'size_kb': filename.stat().st_size / 1024
    })
    print(f"✅ Colors")
    
    # Coloring
    index['coloring'] = []
    filename = ASSETS_DIR / 'coloring' / 'coloring_01.jpg'
    filename.parent.mkdir(exist_ok=True)
    generate_coloring_worksheet(filename)
    index['coloring'].append({
        'id': 1,
        'idea': 'Happy sun coloring page',
        'image': f'assets/worksheets/coloring/coloring_01.jpg',
        'size_kb': filename.stat().st_size / 1024
    })
    print(f"✅ Coloring")
    
    # Save index
    index_path = ASSETS_DIR / 'index.json'
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\n✅ Complete! Index saved to {index_path}")
    return True

if __name__ == "__main__":
    main()
