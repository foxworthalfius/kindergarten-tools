"""
Kindergarten Teacher Tools - Worksheet & Activity Generator
FastAPI web app for a kindergarten assistant teacher
"""

from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List
from io import BytesIO
import random
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import requests
from urllib.request import urlopen

app = FastAPI(title="Kindergarten Teacher Tools", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# DATA MODELS
# =====================

class WorksheetRequest(BaseModel):
    category: str  # letters, numbers, shapes, colors, mazes, coloring
    difficulty: str  # easy, medium, hard
    count: int = 1
    age_range: str = "3-5"

class ActivityRequest(BaseModel):
    category: str  # indoor, creative, movement, calm, social
    duration_minutes: int = 15
    count: int = 3
    age_range: str = "3-5"

class IdeaRequest(BaseModel):
    type: str  # worksheet, activity, game
    theme: Optional[str] = None  # animals, space, ocean, weather, etc.
    count: int = 3

# =====================
# CONTENT DATABASE
# =====================

WORKSHEETS = {
    "letters": {
        "easy": [
            "Letter A tracing worksheet with apple example",
            "Letter B tracing with bubble outlines",
            "Letter C tracing with cat face",
            "Letter D tracing with dog paws",
            "Find and circle all letter A's in a row of letters"
        ],
        "medium": [
            "Fill in the missing letters in the alphabet sequence",
            "Match uppercase letters to lowercase letters",
            "Letter sounds - circle pictures that start with 'T'",
            "Unscramble the letters to make a word",
            "Write the first letter of each picture"
        ],
        "hard": [
            "Write 3 words that start with each letter",
            "Letter maze - follow A-B-C-D-E to find the path",
            "Complete the word by adding missing letters",
            "Match words to their beginning sounds",
            "Write a sentence using 5 words from the letter"
        ]
    },
    "numbers": {
        "easy": [
            "Count the apples and circle the correct number (1-5)",
            "Number tracing 1-10 with dotted fonts",
            "Color by number - simple pictures (1-3)",
            "Count and write the number of shapes",
            "Cut and paste - match number to quantity"
        ],
        "medium": [
            "Simple addition with pictures (sums to 10)",
            "Number sequence - fill in the missing numbers",
            "Count by 2s - connect the dots",
            "Tally marks worksheet (1-20)",
            "Before and after - what number comes before/after"
        ],
        "hard": [
            "Simple subtraction with pictures",
            "Number bonds to 10",
            "Count objects and write the total",
            "Greater than / less than comparison",
            "Simple word problems with pictures"
        ]
    },
    "shapes": {
        "easy": [
            "Trace and color circles, squares, triangles",
            "Find all the circles in the picture",
            "Shape matching - draw a line to match shapes",
            "Color the shapes by name",
            "Trace the basic shapes (circle, square, triangle, rectangle)"
        ],
        "medium": [
            "How many sides does each shape have?",
            "Complete the pattern (circle, square, circle, ?)",
            "Draw the shape that comes next",
            "Match real-world objects to their shapes",
            "Count edges and corners of each shape"
        ],
        "hard": [
            "Identify 2D vs 3D shapes",
            "Draw lines of symmetry",
            "Combine shapes to make pictures",
            "Shape patterns with increasing complexity",
            "Build 3D shapes from nets"
        ]
    },
    "colors": {
        "easy": [
            "Color the apple red, sky blue, grass green",
            "Match the color word to the correct color",
            "Color by number with primary colors",
            "Circle all the red items in the picture",
            "Paint chip color matching"
        ],
        "medium": [
            "Color mixing - what happens when you mix red + blue?",
            "Complete the color pattern (red, blue, red, ?)",
            "Rainbow sequencing worksheet",
            "Match the object to its natural color",
            "Color subtraction - paint over to see the answer"
        ],
        "hard": [
            "Identify shades (light blue vs dark blue)",
            "Color theory basics - complementary colors",
            "Create your own color by number",
            "Match colors to feelings/emotions",
            "Weather and color association"
        ]
    },
    "mazes": {
        "easy": [
            "Simple maze - find the path from start to finish",
            "Help the bee find the flower (easy maze)",
            "Simple grid maze (5x5)",
            "Animal maze - help the cat find home",
            "Straight path maze with few turns"
        ],
        "medium": [
            "Medium maze with some dead ends",
            "Help the astronaut find the rocket",
            "Grid maze (7x7)",
            "Find two paths through the maze",
            "Themed maze with obstacles"
        ],
        "hard": [
            "Complex maze with multiple dead ends",
            "Multi-level maze puzzle",
            "Grid maze (10x10)",
            "Speed maze - find the fastest path",
            "Create your own maze worksheet"
        ]
    },
    "coloring": {
        "easy": [
            "Simple outline - big shapes to color",
            "Cute dinosaur coloring page",
            "Friendly farm animal outlines",
            "Easy butterfly drawing to color",
            "Big dashed outlines for small hands"
        ],
        "medium": [
            "Detailed butterfly with pattern sections",
            "Under the sea scene to color",
            "Jungle animals coloring page",
            "Seasonal scene (spring flowers)",
            "Community helpers coloring (teacher, firefighter)"
        ],
        "hard": [
            "Intricate mandala for kids",
            "Detailed fairy tale scene",
            "Ocean coral reef complex scene",
            "Multi-layered nature scene",
            "Cultural celebration coloring page"
        ]
    }
}

ACTIVITIES = {
    "indoor": [
        {
            "name": "Freeze Dance",
            "description": "Play music and let kids dance freely. When the music stops, everyone freezes!",
            "materials": "Music player, speaker",
            "duration_min": 10,
            "skills": ["Gross motor", "Listening", "Self-control"]
        },
        {
            "name": "Indoor Scavenger Hunt",
            "description": "Give kids a list of items to find around the classroom.",
            "materials": "Printed list, small items to find",
            "duration_min": 15,
            "skills": ["Observation", "Problem-solving", "Movement"]
        },
        {
            "name": "Building Block Challenge",
            "description": "See who can build the tallest tower or recreate a picture with blocks.",
            "materials": "Blocks, LEGOs, or building bricks",
            "duration_min": 20,
            "skills": ["Fine motor", "Creativity", "Persistence"]
        },
        {
            "name": "Story Stone Sequencing",
            "description": "Pull story stones one at a time and create a story from the images.",
            "materials": "Story stones or picture cards",
            "duration_min": 15,
            "skills": ["Language", "Creativity", "Sequencing"]
        },
        {
            "name": "Simon Says",
            "description": "Classic game of following instructions - only follow when preceded by 'Simon Says'.",
            "materials": "None needed",
            "duration_min": 10,
            "skills": ["Listening", "Body awareness", "Following directions"]
        },
        {
            "name": "Indoor Hopscotch",
            "description": "Create a hopscotch grid with tape on the floor.",
            "materials": "Painter's tape",
            "duration_min": 15,
            "skills": ["Gross motor", "Number recognition", "Balance"]
        },
        {
            "name": "Dramatic Play Corner",
            "description": "Set up a pretend play area - restaurant, doctor's office, or store.",
            "materials": "Costume props, toy food, etc.",
            "duration_min": 20,
            "skills": ["Social", "Imagination", "Language"]
        },
        {
            "name": "Puzzle Race",
            "description": "Team up to see how fast you can complete a puzzle together.",
            "materials": "Age-appropriate puzzles",
            "duration_min": 15,
            "skills": ["Teamwork", "Problem-solving", "Patience"]
        }
    ],
    "creative": [
        {
            "name": "Painting with Water",
            "description": "Give kids brushes and water - let them 'paint' on the playground and watch it evaporate!",
            "materials": "Buckets, brushes",
            "duration_min": 20,
            "skills": ["Fine motor", "Creativity", "Exploration"]
        },
        {
            "name": "Collage Creation",
            "description": "Provide magazines, paper scraps, and glue for kids to create collages.",
            "materials": "Magazines, paper scraps, glue sticks, cardstock",
            "duration_min": 25,
            "skills": ["Fine motor", "Creativity", "Decision-making"]
        },
        {
            "name": "Playdough Creations",
            "description": "Let kids sculpt whatever they imagine with playdough.",
            "materials": "Playdough, rolling pins, cookie cutters",
            "duration_min": 20,
            "skills": ["Fine motor", "Creativity", "Sensory"]
        },
        {
            "name": "Finger Painting",
            "description": "Just paint - with fingers! No brushes allowed.",
            "materials": "Washable finger paints, smocks",
            "duration_min": 25,
            "skills": ["Sensory", "Self-expression", "Fine motor"]
        },
        {
            "name": "Paper Airplane Contest",
            "description": "Fold paper airplanes together, then see whose flies the farthest.",
            "materials": "Paper",
            "duration_min": 20,
            "skills": ["Following directions", "Fine motor", "Scientific thinking"]
        }
    ],
    "movement": [
        {
            "name": "Animal Walks",
            "description": "Call out animals and kids walk like that animal around the room.",
            "materials": "None needed",
            "duration_min": 10,
            "skills": ["Gross motor", "Imagination", "Body awareness"]
        },
        {
            "name": "Ball Pass",
            "description": "Sit in a circle and pass a ball while music plays. When music stops, holder answers a question.",
            "materials": "Music player, soft ball",
            "duration_min": 15,
            "skills": ["Turn-taking", "Listening", "Social"]
        },
        {
            "name": "Obstacle Course",
            "description": "Set up stations: crawl under tables, jump over pillows, throw beanbags in baskets.",
            "materials": "Cones, pillows, hula hoops, beanbags",
            "duration_min": 20,
            "skills": ["Gross motor", "Problem-solving", "Balance"]
        },
        {
            "name": "Musical Chairs",
            "description": "Classic game - one less chair than players, music plays, when it stops find a seat!",
            "materials": "Music player, chairs",
            "duration_min": 10,
            "skills": ["Movement", "Turn-taking", "Quick reactions"]
        },
        {
            "name": "Yoga for Kids",
            "description": "Lead kids through simple yoga poses: tree, dog, cat, butterfly.",
            "materials": "Yoga mat or carpet",
            "duration_min": 15,
            "skills": ["Balance", "Flexibility", "Concentration"]
        }
    ],
    "calm": [
        {
            "name": "Breathing Ball",
            "description": "Kids lie on back with ball on tummy, breathe in to raise ball, breathe out to lower.",
            "materials": "Small soft ball",
            "duration_min": 10,
            "skills": ["Self-regulation", "Body awareness", "Relaxation"]
        },
        {
            "name": "Guided Meditation",
            "description": "Lead a simple body scan or visualization exercise.",
            "materials": "Quiet space",
            "duration_min": 10,
            "skills": ["Self-regulation", "Concentration", "Relaxation"]
        },
        {
            "name": "Sand Tray Play",
            "description": "Kids use fingers to draw patterns and shapes in sand trays.",
            "materials": "Sand trays or bins",
            "duration_min": 15,
            "skills": ["Sensory", "Fine motor", "Calm"]
        },
        {
            "name": "Reading Nook Time",
            "description": "Create a cozy corner with pillows and let kids look at books quietly.",
            "materials": "Books, pillows, tent or blanket fort",
            "duration_min": 20,
            "skills": ["Language", "Independence", "Relaxation"]
        },
        {
            "name": "Coloring Calm",
            "description": "Put on soft music and color - no rules, just peaceful creation.",
            "materials": "Coloring pages, crayons",
            "duration_min": 15,
            "skills": ["Focus", "Creativity", "Self-expression"]
        }
    ],
    "social": [
        {
            "name": "Show and Tell",
            "description": "Each child brings something special to share with the group.",
            "materials": "None (kids bring items from home)",
            "duration_min": 20,
            "skills": ["Language", "Confidence", "Listening"]
        },
        {
            "name": "Cooperative Building",
            "description": "Teams work together to build the tallest structure using limited materials.",
            "materials": "Blocks, tape, cardboard",
            "duration_min": 25,
            "skills": ["Teamwork", "Communication", "Problem-solving"]
        },
        {
            "name": "Feelings Charades",
            "description": "Kids act out different emotions, others guess what feeling it is.",
            "materials": "Feelings cards",
            "duration_min": 15,
            "skills": ["Emotional awareness", "Expression", "Observation"]
        },
        {
            "name": "Friendship Circle",
            "description": "Sit in circle, pass a plush toy, holder says something nice about the person next to them.",
            "materials": "Soft plush toy",
            "duration_min": 15,
            "skills": ["Social", "Language", "Kindness"]
        },
        {
            "name": "Group Mural",
            "description": "Large paper on wall - each child adds something to a collaborative art piece.",
            "materials": "Large paper, markers, crayons",
            "duration_min": 30,
            "skills": ["Collaboration", "Creativity", "Sharing"]
        }
    ]
}

THEMES = ["animals", "space", "ocean", "weather", "food", "transportation", "nature", "fairy-tales", "sports", "music"]

# =====================
# API ENDPOINTS
# =====================

@app.get("/", response_class=HTMLResponse)
async def home():
    return get_home_page()

@app.get("/api/worksheets")
async def generate_worksheets(
    category: str = "letters",
    difficulty: str = "easy",
    count: int = 5
):
    """Generate worksheet ideas"""
    if category not in WORKSHEETS:
        raise HTTPException(400, f"Unknown category: {category}")
    if difficulty not in WORKSHEETS[category]:
        raise HTTPException(400, f"Unknown difficulty: {difficulty}")
    
    ideas = random.sample(WORKSHEETS[category][difficulty], min(count, len(WORKSHEETS[category][difficulty])))
    return {
        "category": category,
        "difficulty": difficulty,
        "ideas": ideas,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/activities")
async def generate_activities(
    category: str = "indoor",
    count: int = 3,
    duration_minutes: int = 15
):
    """Generate indoor activity ideas"""
    if category not in ACTIVITIES:
        raise HTTPException(400, f"Unknown category: {category}")
    
    # Filter by duration
    filtered = [a for a in ACTIVITIES[category] if a["duration_min"] <= duration_minutes]
    if not filtered:
        filtered = ACTIVITIES[category]
    
    selected = random.sample(filtered, min(count, len(filtered)))
    return {
        "category": category,
        "activities": selected,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/categories")
async def get_categories():
    """Get all available categories"""
    return {
        "worksheets": list(WORKSHEETS.keys()),
        "activities": list(ACTIVITIES.keys()),
        "themes": THEMES,
        "difficulties": ["easy", "medium", "hard"]
    }

@app.get("/api/ideas")
async def get_ideas(
    type: str = "worksheet",
    theme: str = None,
    count: int = 3
):
    """Get themed ideas"""
    if type == "worksheet":
        category = random.choice(list(WORKSHEETS.keys()))
        difficulty = random.choice(["easy", "medium", "hard"])
        ideas = random.sample(WORKSHEETS[category][difficulty], min(count, 3))
        return {"type": "worksheet", "category": category, "difficulty": difficulty, "ideas": ideas}
    elif type == "activity":
        cat = random.choice(list(ACTIVITIES.keys()))
        acts = random.sample(ACTIVITIES[cat], min(count, len(ACTIVITIES[cat])))
        return {"type": "activity", "category": cat, "activities": acts}
    else:
        raise HTTPException(400, f"Unknown type: {type}")

# =====================
# IMAGE GENERATION (B&W Outlines)
# =====================

def draw_simple_outline(draw, center_x, center_y, size, shape_type):
    """Draw simple black outline shapes"""
    half = size // 2
    if shape_type == "circle":
        draw.ellipse([center_x - half, center_y - half, center_x + half, center_y + half], outline="black", width=3)
    elif shape_type == "square":
        draw.rectangle([center_x - half, center_y - half, center_x + half, center_y + half], outline="black", width=3)
    elif shape_type == "triangle":
        points = [
            (center_x, center_y - half),
            (center_x - half, center_y + half),
            (center_x + half, center_y + half)
        ]
        draw.polygon(points, outline="black", width=3)
    elif shape_type == "star":
        # Simple 5-point star
        points = []
        for i in range(10):
            angle = i * 36 - 90
            r = half if i % 2 == 0 else half // 2
            x = center_x + r * (1 if i % 2 == 0 else 0.5) * (1 if angle < 180 else -1 if angle > 180 else 0)
            y = center_y + r * 0.9 * (-1 if angle < 180 else 1)
            # Approximate star points manually
            pass
        # Simple star using polygon
        cx, cy = center_x, center_y
        r_outer, r_inner = half, half // 2
        points = []
        for i in range(5):
            angle_start = i * 72 - 90
            points.append((cx + r_outer * cos(angle_start * pi / 180), cy + r_outer * sin(angle_start * pi / 180)))
            points.append((cx + r_inner * cos((angle_start + 36) * pi / 180), cy + r_inner * sin((angle_start + 36) * pi / 180)))
        draw.polygon(points, outline="black", width=3)

def draw_activity_icon(draw, x, y, size, activity_name):
    """Draw a simple black outline icon representing an activity"""
    half = size // 2
    cx, cy = x, y
    
    name_lower = activity_name.lower()
    
    if "freeze dance" in name_lower or "dance" in name_lower:
        # Dancing figure - simple stick figure in dance pose
        # Head
        draw.ellipse([cx - 8, cy - 30, cx + 8, cy - 14], outline="black", width=2)
        # Body
        draw.line([cx, cy - 14, cx, cy + 10], fill="black", width=2)
        # Arms up in dance pose
        draw.line([cx, cy - 5, cx - 18, cy - 20], fill="black", width=2)
        draw.line([cx, cy - 5, cx + 18, cy - 15], fill="black", width=2)
        # Legs in dance stance
        draw.line([cx, cy + 10, cx - 12, cy + 35], fill="black", width=2)
        draw.line([cx, cy + 10, cx + 15, cy + 30], fill="black", width=2)
        
    elif "scavenger" in name_lower:
        # Magnifying glass
        draw.ellipse([cx - 12, cy - 22, cx + 12, cy - 2], outline="black", width=2)
        draw.line([cx + 8, cy + 5, cx + 22, cy + 20], fill="black", width=2)
        
    elif "block" in name_lower or "building" in name_lower:
        # Stacked blocks
        draw.rectangle([cx - 20, cy - 5, cx - 5, cy + 15], outline="black", width=2)
        draw.rectangle([cx + 5, cy - 5, cx + 20, cy + 15], outline="black", width=2)
        draw.rectangle([cx - 8, cy - 25, cx + 8, cy - 5], outline="black", width=2)
        
    elif "story" in name_lower or "stone" in name_lower:
        # Book
        draw.rectangle([cx - 15, cy - 20, cx + 15, cy + 20], outline="black", width=2)
        draw.line([cx, cy - 20, cx, cy + 20], fill="black", width=2)
        
    elif "simon says" in name_lower:
        # Ear/listening
        draw.arc([cx - 15, cy - 20, cx + 10, cy + 15], 200, 340, fill="black", width=2)
        draw.line([cx - 5, cy, cx + 5, cy], fill="black", width=2)
        
    elif "hopscotch" in name_lower:
        # Numbers/grid
        for i, (hx, hy) in enumerate([(cx, cy - 18), (cx - 12, cy - 3), (cx + 12, cy - 3), (cx - 18, cy + 15), (cx, cy + 15), (cx + 18, cy + 15)]):
            draw.ellipse([hx - 6, hy - 6, hx + 6, hy + 6], outline="black", width=2)
            
    elif "dramatic" in name_lower or "pretend" in name_lower:
        # Mask/theater
        draw.ellipse([cx - 18, cy - 12, cx + 18, cy + 12], outline="black", width=2)
        draw.ellipse([cx - 10, cy - 6, cx - 3, cy + 2], outline="black", width=2)
        draw.ellipse([cx + 3, cy - 6, cx + 10, cy + 2], outline="black", width=2)
        draw.arc([cx - 8, cy + 2, cx + 8, cy + 12], 0, 180, fill="black", width=2)
        
    elif "puzzle" in name_lower:
        # Puzzle piece outline
        draw.polygon([(cx - 18, cy - 8), (cx - 8, cy - 8), (cx - 8, cy - 15), (cx + 2, cy - 15), (cx + 2, cy - 8), (cx + 18, cy - 8), (cx + 18, cy + 8), (cx + 8, cy + 8), (cx + 8, cy + 15), (cx - 2, cy + 15), (cx - 2, cy + 8), (cx - 18, cy + 8)], outline="black", width=2)
        
    elif "painting" in name_lower or "paint" in name_lower:
        # Paintbrush
        draw.rectangle([cx - 3, cy - 22, cx + 3, cy + 5], outline="black", width=2)
        draw.ellipse([cx - 8, cy + 5, cx + 8, cy + 18], outline="black", width=2)
        
    elif "collage" in name_lower:
        # Scissors and paper
        draw.rectangle([cx - 15, cy - 18, cx + 10, cy + 15], outline="black", width=2)
        draw.arc([cx + 5, cy + 5, cx + 20, cy + 20], 45, 135, fill="black", width=2)
        
    elif "playdough" in name_lower:
        # Rolling pin
        draw.rectangle([cx - 18, cy - 5, cx + 18, cy + 5], outline="black", width=2)
        draw.line([cx - 18, cy - 5, cx - 22, cy - 8], fill="black", width=2)
        draw.line([cx - 18, cy + 5, cx - 22, cy + 8], fill="black", width=2)
        draw.line([cx + 18, cy - 5, cx + 22, cy - 8], fill="black", width=2)
        draw.line([cx + 18, cy + 5, cx + 22, cy + 8], fill="black", width=2)
        
    elif "finger paint" in name_lower:
        # Handprint
        draw.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], outline="black", width=2)
        for dx, dy in [(-18, -20), (-8, -25), (0, -22), (10, -25), (18, -18)]:
            draw.ellipse([cx + dx - 5, cy + dy - 5, cx + dx + 5, cy + dy + 5], outline="black", width=2)
            
    elif "paper airplane" in name_lower or "airplane" in name_lower:
        # Paper airplane
        draw.polygon([(cx - 25, cy), (cx + 20, cy - 8), (cx + 15, cy + 8)], outline="black", width=2)
        draw.line([cx - 25, cy, cx + 5, cy + 5], fill="black", width=2)
        
    elif "animal walk" in name_lower:
        # Simple bear/ animal paw
        draw.ellipse([cx - 12, cy - 5, cx + 12, cy + 10], outline="black", width=2)
        for dx, dy in [(-15, -18), (-5, -22), (5, -22), (15, -18)]:
            draw.ellipse([cx + dx - 4, cy + dy - 4, cx + dx + 4, cy + dy + 4], outline="black", width=2)
            
    elif "ball pass" in name_lower or "ball" in name_lower:
        # Ball
        draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline="black", width=2)
        draw.arc([cx - 18, cy - 18, cx + 18, cy + 18], -60, 240, fill="black", width=2)
        
    elif "obstacle" in name_lower:
        # Flag/marker
        draw.line([cx - 15, cy + 25, cx - 15, cy - 25], fill="black", width=2)
        draw.polygon([(cx - 15, cy - 25), (cx + 15, cy - 18), (cx - 15, cy - 10)], outline="black", width=2)
        
    elif "musical chair" in name_lower:
        # Chair
        draw.rectangle([cx - 12, cy - 5, cx + 12, cy + 25], outline="black", width=2)
        draw.line([cx - 12, cy - 5, cx - 18, cy - 20], fill="black", width=2)
        draw.line([cx + 12, cy - 5, cx + 18, cy - 20], fill="black", width=2)
        
    elif "yoga" in name_lower:
        # Lotus position
        draw.ellipse([cx - 10, cy - 25, cx + 10, cy - 5], outline="black", width=2)  # Head
        draw.line([cx, cy - 5, cx, cy + 10], fill="black", width=2)  # Body
        draw.arc([cx - 20, cy + 5, cx + 20, cy + 25], 0, 180, fill="black", width=2)  # Crossed legs
        
    elif "breathing" in name_lower:
        # Lungs/breath
        draw.arc([cx - 18, cy - 15, cx, cy + 15], -90, 90, fill="black", width=2)
        draw.arc([cx, cy - 15, cx + 18, cy + 15], 90, 270, fill="black", width=2)
        
    elif "meditation" in name_lower or "calm" in name_lower:
        # Om symbol simplified
        draw.arc([cx - 15, cy - 18, cx + 15, cy + 18], -150, 150, fill="black", width=3)
        draw.arc([cx - 10, cy - 12, cx + 10, cy + 12], 30, 210, fill="black", width=2)
        
    elif "sand" in name_lower:
        # Sandal/foot
        draw.ellipse([cx - 15, cy - 8, cx + 15, cy + 12], outline="black", width=2)
        for dx, dy in [(-10, -18), (0, -20), (10, -18)]:
            draw.ellipse([cx + dx - 3, cy + dy - 3, cx + dx + 3, cy + dy + 3], outline="black", width=2)
            
    elif "reading" in name_lower or "book" in name_lower:
        # Open book
        draw.polygon([(cx - 20, cy - 15), (cx, cy + 5), (cx, cy + 20), (cx - 20, cy)], outline="black", width=2)
        draw.polygon([(cx + 20, cy - 15), (cx, cy + 5), (cx, cy + 20), (cx + 20, cy)], outline="black", width=2)
        
    elif "coloring" in name_lower:
        # Crayon
        draw.rectangle([cx - 5, cy - 25, cx + 5, cy + 20], outline="black", width=2)
        draw.polygon([(cx - 5, cy - 25), (cx, cy - 35), (cx + 5, cy - 25)], outline="black", width=2)
        
    elif "show and tell" in name_lower:
        # Microphone
        draw.ellipse([cx - 10, cy - 25, cx + 10, cy - 5], outline="black", width=2)
        draw.line([cx, cy - 5, cx, cy + 25], fill="black", width=2)
        draw.rectangle([cx - 8, cy + 25, cx + 8, cy + 35], outline="black", width=2)
        
    elif "cooperative" in name_lower or "team" in name_lower:
        # Two hands together
        draw.ellipse([cx - 20, cy - 5, cx - 5, cy + 10], outline="black", width=2)
        draw.ellipse([cx + 5, cy - 5, cx + 20, cy + 10], outline="black", width=2)
        
    elif "feelings" in name_lower or "charades" in name_lower:
        # Face outline
        draw.ellipse([cx - 20, cy - 25, cx + 20, cy + 20], outline="black", width=2)
        draw.ellipse([cx - 10, cy - 15, cx - 3, cy - 8], outline="black", width=2)
        draw.ellipse([cx + 3, cy - 15, cx + 10, cy - 8], outline="black", width=2)
        draw.arc([cx - 10, cy + 5, cx + 10, cy + 15], 0, 180, fill="black", width=2)
        
    elif "friendship" in name_lower or "circle" in name_lower:
        # Heart
        draw.arc([cx - 15, cy - 15, cx, cy], -180, 0, fill="black", width=2)
        draw.arc([cx, cy - 15, cx + 15, cy], -180, 0, fill="black", width=2)
        draw.line([cx - 15, cy, cx, cy + 20], fill="black", width=2)
        draw.line([cx + 15, cy, cx, cy + 20], fill="black", width=2)
        
    elif "mural" in name_lower or "group" in name_lower:
        # Palette
        draw.ellipse([cx - 25, cy - 15, cx + 25, cy + 20], outline="black", width=2)
        draw.ellipse([cx - 5, cy - 20, cx + 5, cy - 10], outline="black", width=2)
        for dx, dy in [(-18, -5), (-8, -8), (8, -8), (18, -5), (20, 5)]:
            draw.ellipse([cx + dx - 4, cy + dy - 4, cx + dx + 4, cy + dy + 4], outline="black", width=2)
        
    else:
        # Default: simple star
        cx, cy = x, y
        r_outer, r_inner = half, half // 2
        from math import cos, sin, pi
        points = []
        for i in range(5):
            angle_start = i * 72 - 90
            points.append((cx + r_outer * cos(angle_start * pi / 180), cy + r_outer * sin(angle_start * pi / 180)))
            points.append((cx + r_inner * cos((angle_start + 36) * pi / 180), cy + r_inner * sin((angle_start + 36) * pi / 180)))
        draw.polygon(points, outline="black", width=3)

def generate_activity_image(activity_name: str) -> bytes:
    """Generate a simple B&W outline image for an activity"""
    from math import cos, sin, pi
    
    # Canvas size
    width, height = 400, 300
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([5, 5, width - 5, height - 5], outline="black", width=2)
    
    # Draw activity icon in center
    icon_size = 80
    icon_x, icon_y = width // 2, 80
    draw_activity_icon(draw, icon_x, icon_y, icon_size, activity_name)
    
    # Draw activity name
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    # Word wrap the activity name
    words = activity_name.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > 350:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
        else:
            current_line.append(word)
    if current_line:
        lines.append(' '.join(current_line))
    
    y_text = 170
    for line in lines[:2]:  # Max 2 lines
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((width // 2 - text_width // 2, y_text), line, fill="black", font=font)
        y_text += 28
    
    # Draw some decorative elements based on activity type
    name_lower = activity_name.lower()
    
    # Draw small icons around the border to represent the activity category
    if any(w in name_lower for w in ["dance", "freeze", "music"]):
        # Musical notes
        for nx, ny in [(50, 250), (350, 250), (100, 270), (300, 270)]:
            draw.ellipse([nx - 8, ny - 8, nx + 8, ny + 8], outline="black", width=2)
            draw.rectangle([nx + 6, ny - 20, nx + 8, ny - 8], outline="black", width=2)
            
    elif any(w in name_lower for w in ["craft", "paint", "art", "create"]):
        # Paint dots
        for px, py in [(50, 250), (350, 250), (200, 270), (100, 270), (300, 270)]:
            draw.ellipse([px - 5, py - 5, px + 5, py + 5], outline="black", width=2)
            
    elif any(w in name_lower for w in ["read", "book", "story"]):
        # Book shapes
        draw.rectangle([60, 245, 90, 275], outline="black", width=2)
        draw.rectangle([310, 245, 340, 275], outline="black", width=2)
        
    else:
        # Default dots
        for dx, dy in [(60, 260), (340, 260), (100, 275), (300, 275)]:
            draw.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], outline="black", width=2)
    
    # Draw "Activity Idea" label at bottom
    draw.text((width // 2 - 50, 285), "Activity Idea", fill="black", font=small_font)
    
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()

@app.get("/api/activity-image")
async def get_activity_image(activity: str = "Freeze Dance"):
    """Generate a B&W outline image for an activity"""
    try:
        img_bytes = generate_activity_image(activity)
        return StreamingResponse(img_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(500, f"Error generating image: {str(e)}")

def generate_worksheet_content_image(idea: str, category: str) -> Image.Image:
    """Generate high-quality worksheet content using PIL (production quality)"""
    from PIL import Image, ImageDraw, ImageFont
    import re
    
    # Higher resolution for better quality
    width, height = 800, 600
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to load nice fonts
    try:
        # Try multiple font paths for better compatibility
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
        ]
        font_large = None
        font_med = None
        font_small = None
        
        for font_path in font_paths:
            try:
                font_large = ImageFont.truetype(font_path, 96)
                font_med = ImageFont.truetype(font_path, 48)
                font_small = ImageFont.truetype(font_path, 28)
                break
            except:
                continue
        
        if not font_large:
            font_large = ImageFont.load_default()
            font_med = font_large
            font_small = font_large
    except:
        font_large = ImageFont.load_default()
        font_med = font_large
        font_small = font_large
    
    # Thicker border for better appearance
    draw.rectangle([20, 20, width-20, height-20], outline="black", width=3)
    
    if category == "letters":
        # Extract letter from idea
        match = re.search(r'[A-Z]', idea)
        if match:
            letter = match.group().upper()
            # Center the letter
            bbox = draw.textbbox((0, 0), letter, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = 150
            
            # Draw letter with outline effect
            draw.text((x, y), letter, fill="black", font=font_large)
            
            # Add tracing guide lines with arrows
            y_pos = 320
            for i in range(4):
                # Main tracing line
                draw.line([(100, y_pos), (700, y_pos)], fill=(100, 100, 100), width=2)
                # Add dash effect for tracing feel
                for x_dash in range(120, 680, 20):
                    draw.line([(x_dash, y_pos), (x_dash+8, y_pos)], fill="black", width=2)
                
                # Label
                draw.text((60, y_pos - 10), f"Trace line {i+1}:", fill="black", font=font_med)
                y_pos += 60
                
    elif category == "numbers":
        # Extract number from idea
        match = re.search(r'\d+', idea)
        if match:
            number = match.group()
            # Center the number
            bbox = draw.textbbox((0, 0), number, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = 150
            
            draw.text((x, y), number, fill="black", font=font_large)
            
            # Number tracing lines
            y_pos = 320
            for i in range(3):
                draw.line([(100, y_pos), (700, y_pos)], fill=(100, 100, 100), width=2)
                # Dashed effect
                for x_dash in range(120, 680, 25):
                    draw.line([(x_dash, y_pos), (x_dash+10, y_pos)], fill="black", width=2)
                
                draw.text((60, y_pos - 8), f"Practice {i+1}:", fill="black", font=font_med)
                y_pos += 50
                
    elif category == "shapes":
        # Draw shapes with labels
        shapes = [
            ("Circle", lambda d: d.ellipse([150, 100, 250, 200], outline="black", width=3)),
            ("Square", lambda d: d.rectangle([300, 100, 400, 200], outline="black", width=3)),
            ("Triangle", lambda d: d.polygon([(450, 200), (500, 100), (550, 200)], outline="black", width=3)),
            ("Rectangle", lambda d: d.rectangle([150, 250, 350, 350], outline="black", width=3)),
            ("Diamond", lambda d: d.polygon([(300, 150), (350, 100), (400, 150), (350, 200)], outline="black", width=3)),
        ]
        
        for i, (name, draw_func) in enumerate(shapes):
            col = i % 3
            row = i // 3
            x_offset = 100 + col * 200
            y_offset = 100 + row * 180
            
            # Temporarily translate drawing context
            # Instead, we'll draw each shape at its position
            if name == "Circle":
                draw.ellipse([x_offset, y_offset, x_offset+100, y_offset+100], outline="black", width=3)
            elif name == "Square":
                draw.rectangle([x_offset, y_offset, x_offset+100, y_offset+100], outline="black", width=3)
            elif name == "Triangle":
                draw.polygon([(x_offset+50, y_offset), (x_offset, y_offset+100), (x_offset+100, y_offset+100)], outline="black", width=3)
            elif name == "Rectangle":
                draw.rectangle([x_offset, y_offset, x_offset+100, y_offset+100], outline="black", width=3)
            elif name == "Diamond":
                draw.polygon([(x_offset+50, y_offset), (x_offset, y_offset+50), (x_offset+50, y_offset+100), (x_offset+100, y_offset+50)], outline="black", width=3)
            
            # Label below shape
            text_bbox = draw.textbbox((0, 0), name, font=font_med)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((x_offset + (100 - text_width)//2, y_offset + 110), name, fill="black", font=font_med)
                
    elif category == "mazes":
        # Draw a nice maze
        maze_margin = 100
        maze_width = width - 2 * maze_margin
        maze_height = height - 2 * maze_margin
        
        # Outer boundary
        draw.rectangle([maze_margin, maze_margin, width-maze_margin, height-maze_margin], outline="black", width=3)
        
        # Start and end
        draw.ellipse([maze_margin+10, maze_margin+10, maze_margin+40, maze_margin+40], fill="green", outline="black", width=2)
        draw.text((maze_margin+45, maze_margin+15), "Start", fill="black", font=font_med)
        
        draw.ellipse([width-maze_margin-40, height-maze_margin-40, width-maze_margin-10, height-maze_margin-10], fill="red", outline="black", width=2)
        draw.text((width-maze_margin-35, height-maze_margin-15), "End", fill="black", font=font_med)
        
        # Draw maze paths (simple maze)
        # Horizontal paths
        draw.line([(maze_margin+50, maze_margin+100), (width-maze_margin-50, maze_margin+100)], fill="black", width=3)
        draw.line([(maze_margin+50, maze_margin+200), (maze_margin+200, maze_margin+200)], fill="black", width=3)
        draw.line([(maze_margin+200, maze_margin+200), (maze_margin+200, height-maze_margin-100)], fill="black", width=3)
        draw.line([(maze_margin+100, maze_margin+300), (width-maze_margin-100, maze_margin+300)], fill="black", width=3)
        draw.line([(width-maze_margin-100, maze_margin+300), (width-maze_margin-100, height-maze_margin-50)], fill="black", width=3)
        
        # Vertical paths
        draw.line([(maze_margin+100, maze_margin+100), (maze_margin+100, maze_margin+200)], fill="black", width=3)
        draw.line([(maze_margin+300, maze_margin+100), (maze_margin+300, maze_margin+300)], fill="black", width=3)
        draw.line([(width-maze_margin-100, maze_margin+200), (width-maze_margin-100, height-maze_margin-100)], fill="black", width=3)
        
        # Label
        draw.text((width//2, height-50), "Find the path from Start to End!", fill="black", font=font_med)
        
    elif category == "colors":
        # Draw color swatches with names
        colors = [
            ("Red", (255, 100, 100)),
            ("Blue", (100, 100, 255)),
            ("Yellow", (255, 255, 100)),
            ("Green", (100, 200, 100)),
            ("Orange", (255, 165, 0)),
            ("Purple", (200, 100, 255))
        ]
        
        for i, (name, rgb) in enumerate(colors):
            col = i % 3
            row = i // 3
            x = 100 + col * 200
            y = 100 + row * 150
            
            # Color swatch
            draw.rectangle([x, y, x+120, y+100], fill=rgb, outline="black", width=2)
            
            # Color name
            text_bbox = draw.textbbox((0, 0), name, font=font_med)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((x + (120 - text_width)//2, y+110), name, fill="black", font=font_med)
            
    elif category == "coloring":
        # Draw a fun character to color
        # Simple smiling sun
        draw.ellipse([300, 100, 500, 300], outline="black", width=3)  # Sun face
        draw.ellipse([350, 150, 380, 180], outline="black", width=2)  # Left eye
        draw.ellipse([420, 150, 450, 180], outline="black", width=2)  # Right eye
        draw.arc([325, 200, 475, 300], 0, 180, fill="black", width=3)  # Smile
        
        # Sun rays
        for i in range(12):
            angle = i * 30
            import math
            x1 = 400 + int(120 * math.cos(math.radians(angle)))
            y1 = 200 + int(120 * math.sin(math.radians(angle)))
            x2 = 400 + int(180 * math.cos(math.radians(angle)))
            y2 = 200 + int(180 * math.sin(math.radians(angle)))
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
        
        draw.text((width//2, 350), "Color the Happy Sun!", fill="black", font=font_med)
    
    return img

def generate_fallback_worksheet_image(idea: str, category: str) -> Image.Image:
    """Generate high-quality worksheet content using PIL (production quality)"""
    from PIL import Image, ImageDraw, ImageFont
    import re
    
    # Higher resolution for better quality
    width, height = 800, 600
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to load nice fonts
    try:
        # Try multiple font paths for better compatibility
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
        ]
        font_large = None
        font_med = None
        font_small = None
        
        for font_path in font_paths:
            try:
                font_large = ImageFont.truetype(font_path, 96)
                font_med = ImageFont.truetype(font_path, 48)
                font_small = ImageFont.truetype(font_path, 28)
                break
            except:
                continue
        
        if not font_large:
            font_large = ImageFont.load_default()
            font_med = font_large
            font_small = font_large
    except:
        font_large = ImageFont.load_default()
        font_med = font_large
        font_small = font_large
    
    # Thicker border for better appearance
    draw.rectangle([20, 20, width-20, height-20], outline="black", width=3)
    
    if category == "letters":
        # Extract letter from idea
        match = re.search(r'[A-Z]', idea)
        if match:
            letter = match.group().upper()
            # Center the letter
            bbox = draw.textbbox((0, 0), letter, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = 150
            
            # Draw letter with outline effect
            draw.text((x, y), letter, fill="black", font=font_large)
            
            # Add tracing guide lines with arrows
            y_pos = 320
            for i in range(4):
                # Main tracing line
                draw.line([(100, y_pos), (700, y_pos)], fill=(100, 100, 100), width=2)
                # Add dash effect for tracing feel
                for x_dash in range(120, 680, 20):
                    draw.line([(x_dash, y_pos), (x_dash+8, y_pos)], fill="black", width=2)
                
                # Label
                draw.text((60, y_pos - 10), f"Trace line {i+1}:", fill="black", font=font_med)
                y_pos += 60
                
    elif category == "numbers":
        # Extract number from idea
        match = re.search(r'\d+', idea)
        if match:
            number = match.group()
            # Center the number
            bbox = draw.textbbox((0, 0), number, font=font_large)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = 150
            
            draw.text((x, y), number, fill="black", font=font_large)
            
            # Number tracing lines
            y_pos = 320
            for i in range(3):
                draw.line([(100, y_pos), (700, y_pos)], fill=(100, 100, 100), width=2)
                # Dashed effect
                for x_dash in range(120, 680, 25):
                    draw.line([(x_dash, y_pos), (x_dash+10, y_pos)], fill="black", width=2)
                
                draw.text((60, y_pos - 8), f"Practice {i+1}:", fill="black", font=font_med)
                y_pos += 50
                
    elif category == "shapes":
        # Draw shapes with labels
        shapes = [
            ("Circle", lambda d: d.ellipse([150, 100, 250, 200], outline="black", width=3)),
            ("Square", lambda d: d.rectangle([300, 100, 400, 200], outline="black", width=3)),
            ("Triangle", lambda d: d.polygon([(450, 200), (500, 100), (550, 200)], outline="black", width=3)),
            ("Rectangle", lambda d: d.rectangle([150, 250, 350, 350], outline="black", width=3)),
            ("Diamond", lambda d: d.polygon([(300, 150), (350, 100), (400, 150), (350, 200)], outline="black", width=3)),
        ]
        
        for i, (name, draw_func) in enumerate(shapes):
            col = i % 3
            row = i // 3
            x_offset = 100 + col * 200
            y_offset = 100 + row * 180
            
            # Temporarily translate drawing context
            # Instead, we'll draw each shape at its position
            if name == "Circle":
                draw.ellipse([x_offset, y_offset, x_offset+100, y_offset+100], outline="black", width=3)
            elif name == "Square":
                draw.rectangle([x_offset, y_offset, x_offset+100, y_offset+100], outline="black", width=3)
            elif name == "Triangle":
                draw.polygon([(x_offset+50, y_offset), (x_offset, y_offset+100), (x_offset+100, y_offset+100)], outline="black", width=3)
            elif name == "Rectangle":
                draw.rectangle([x_offset, y_offset, x_offset+100, y_offset+100], outline="black", width=3)
            elif name == "Diamond":
                draw.polygon([(x_offset+50, y_offset), (x_offset, y_offset+50), (x_offset+50, y_offset+100), (x_offset+100, y_offset+50)], outline="black", width=3)
            
            # Label below shape
            text_bbox = draw.textbbox((0, 0), name, font=font_med)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((x_offset + (100 - text_width)//2, y_offset + 110), name, fill="black", font=font_med)
                
    elif category == "mazes":
        # Draw a nice maze
        maze_margin = 100
        maze_width = width - 2 * maze_margin
        maze_height = height - 2 * maze_margin
        
        # Outer boundary
        draw.rectangle([maze_margin, maze_margin, width-maze_margin, height-maze_margin], outline="black", width=3)
        
        # Start and end
        draw.ellipse([maze_margin+10, maze_margin+10, maze_margin+40, maze_margin+40], fill="green", outline="black", width=2)
        draw.text((maze_margin+45, maze_margin+15), "Start", fill="black", font=font_med)
        
        draw.ellipse([width-maze_margin-40, height-maze_margin-40, width-maze_margin-10, height-maze_margin-10], fill="red", outline="black", width=2)
        draw.text((width-maze_margin-35, height-maze_margin-15), "End", fill="black", font=font_med)
        
        # Draw maze paths (simple maze)
        # Horizontal paths
        draw.line([(maze_margin+50, maze_margin+100), (width-maze_margin-50, maze_margin+100)], fill="black", width=3)
        draw.line([(maze_margin+50, maze_margin+200), (maze_margin+200, maze_margin+200)], fill="black", width=3)
        draw.line([(maze_margin+200, maze_margin+200), (maze_margin+200, height-maze_margin-100)], fill="black", width=3)
        draw.line([(maze_margin+100, maze_margin+300), (width-maze_margin-100, maze_margin+300)], fill="black", width=3)
        draw.line([(width-maze_margin-100, maze_margin+300), (width-maze_margin-100, height-maze_margin-50)], fill="black", width=3)
        
        # Vertical paths
        draw.line([(maze_margin+100, maze_margin+100), (maze_margin+100, maze_margin+200)], fill="black", width=3)
        draw.line([(maze_margin+300, maze_margin+100), (maze_margin+300, maze_margin+300)], fill="black", width=3)
        draw.line([(width-maze_margin-100, maze_margin+200), (width-maze_margin-100, height-maze_margin-100)], fill="black", width=3)
        
        # Label
        draw.text((width//2, height-50), "Find the path from Start to End!", fill="black", font=font_med)
        
    elif category == "colors":
        # Draw color swatches with names
        colors = [
            ("Red", (255, 100, 100)),
            ("Blue", (100, 100, 255)),
            ("Yellow", (255, 255, 100)),
            ("Green", (100, 200, 100)),
            ("Orange", (255, 165, 0)),
            ("Purple", (200, 100, 255))
        ]
        
        for i, (name, rgb) in enumerate(colors):
            col = i % 3
            row = i // 3
            x = 100 + col * 200
            y = 100 + row * 150
            
            # Color swatch
            draw.rectangle([x, y, x+120, y+100], fill=rgb, outline="black", width=2)
            
            # Color name
            text_bbox = draw.textbbox((0, 0), name, font=font_med)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text((x + (120 - text_width)//2, y+110), name, fill="black", font=font_med)
            
    elif category == "coloring":
        # Draw a fun character to color
        # Simple smiling sun
        draw.ellipse([300, 100, 500, 300], outline="black", width=3)  # Sun face
        draw.ellipse([350, 150, 380, 180], outline="black", width=2)  # Left eye
        draw.ellipse([420, 150, 450, 180], outline="black", width=2)  # Right eye
        draw.arc([325, 200, 475, 300], 0, 180, fill="black", width=3)  # Smile
        
        # Sun rays
        for i in range(12):
            angle = i * 30
            import math
            x1 = 400 + int(120 * math.cos(math.radians(angle)))
            y1 = 200 + int(120 * math.sin(math.radians(angle)))
            x2 = 400 + int(180 * math.cos(math.radians(angle)))
            y2 = 200 + int(180 * math.sin(math.radians(angle)))
            draw.line([(x1, y1), (x2, y2)], fill="black", width=3)
        
        draw.text((width//2, 350), "Color the Happy Sun!", fill="black", font=font_med)
    
    return img
    """Generate an actual worksheet content image based on the idea"""
    import re
    
    width, height = 600, 400
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_med = font_large
        font_small = font_large
    
    # Border
    draw.rectangle([10, 10, width-10, height-10], outline="black", width=2)
    
    if category == "letters":
        # Extract letter from idea (usually first letter mentioned)
        match = re.search(r'[A-Z]', idea)
        if match:
            letter = match.group()
            # Draw big letter
            draw.text((150, 50), letter, fill="black", font=font_large)
            # Draw tracing practice lines
            y_pos = 200
            for i in range(3):
                draw.line([(50, y_pos), (550, y_pos)], fill=(200, 200, 200), width=1)
                draw.text((30, y_pos - 20), f"Trace:", fill="black", font=font_small)
                y_pos += 50
                
    elif category == "numbers":
        # Extract number from idea
        match = re.search(r'\d+', idea)
        if match:
            number = match.group()
            # Draw big number
            draw.text((200, 50), number, fill="black", font=font_large)
            # Draw tracing lines
            y_pos = 220
            for i in range(3):
                draw.line([(50, y_pos), (550, y_pos)], fill=(200, 200, 200), width=1)
                y_pos += 40
                
    elif category == "shapes":
        # Draw different shapes
        draw.ellipse([50, 50, 150, 150], outline="black", width=3)
        draw.rectangle([180, 50, 280, 150], outline="black", width=3)
        draw.polygon([(320, 150), (370, 50), (420, 150)], outline="black", width=3)
        draw.text((50, 160), "Circle", fill="black", font=font_small)
        draw.text((170, 160), "Square", fill="black", font=font_small)
        draw.text((300, 160), "Triangle", fill="black", font=font_small)
            
    elif category == "mazes":
        # Draw a simple maze
        draw.rectangle([50, 50, 550, 350], outline="black", width=2)
        # Start point
        draw.ellipse([55, 55, 75, 75], fill="green")
        draw.text((80, 60), "START", fill="green", font=font_small)
        # End point
        draw.ellipse([525, 325, 545, 345], fill="red")
        draw.text((480, 330), "END", fill="red", font=font_small)
        # Maze paths
        draw.line([(100, 100), (400, 100)], fill="black", width=3)
        draw.line([(400, 100), (400, 250)], fill="black", width=3)
        draw.line([(100, 150), (300, 150)], fill="black", width=3)
        draw.line([(300, 150), (300, 300)], fill="black", width=3)
        draw.text((200, 200), "Find the path!", fill="black", font=font_med)
        
    elif category == "colors":
        # Draw color boxes
        colors_to_draw = [
            ("Red", (255, 100, 100), 80),
            ("Blue", (100, 100, 255), 220),
            ("Yellow", (255, 255, 100), 360)
        ]
        for color_name, color_rgb, x_pos in colors_to_draw:
            draw.rectangle([x_pos, 100, x_pos + 80, 200], outline="black", width=2)
            draw.text((x_pos + 10, 210), color_name, fill="black", font=font_small)
            
    elif category == "coloring":
        # Draw shapes to color in
        draw.ellipse([100, 80, 300, 280], outline="black", width=3)
        draw.text((150, 300), "Color me!", fill="black", font=font_med)
    
    return img

@app.post("/api/generate-worksheet-pdf")
async def generate_worksheet_pdf(
    idea: str = Form(...),
    category: str = Form("letters"),
    difficulty: str = Form("easy")
):
    """Generate a PDF worksheet from a worksheet idea"""
    try:
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.utils import ImageReader
        
        # Generate worksheet content image
        worksheet_img = generate_worksheet_content_image(idea, category)
        
        # Create PDF buffer
        pdf_buf = BytesIO()
        c = pdf_canvas.Canvas(pdf_buf, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(40, height - 40, f"📝 {category.title()} Worksheet")
        
        # Difficulty level
        c.setFont("Helvetica", 12)
        c.drawString(40, height - 70, f"Difficulty: {difficulty.capitalize()}")
        c.drawString(40, height - 90, f"Date: {datetime.now().strftime('%B %d, %Y')}")
        
        # Add worksheet content image
        img_buf = BytesIO()
        worksheet_img.save(img_buf, format='PNG')
        img_buf.seek(0)
        img_reader = ImageReader(img_buf)
        c.drawImage(img_reader, 40, height - 350, width=500, height=250)
        
        # Instructions box
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 140, "Instructions for Classroom Use:")
        
        c.setFont("Helvetica", 10)
        instructions = [
            "1. Print this worksheet for each student",
            "2. Provide pencils, crayons, or markers as needed",
            "3. Complete the activity as shown",
            "4. Allow students time to complete",
            "5. Review and celebrate their work!"
        ]
        
        y_pos = 120
        for instruction in instructions:
            c.drawString(60, y_pos, instruction)
            y_pos -= 15
        
        # Footer
        c.setFont("Helvetica", 9)
        c.drawString(40, 30, "Created with ❤️ Kindergarten Teacher Tools")
        
        c.save()
        pdf_buf.seek(0)
        
        filename = f"worksheet_{category}_{difficulty}.pdf"
        return StreamingResponse(
            iter([pdf_buf.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(500, f"Error generating PDF: {str(e)}")

# =====================
# WEB PAGE
# =====================

def get_home_page() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kindergarten Teacher Tools 🎨</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        header p { opacity: 0.9; font-size: 1.1rem; }
        
        .card {
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .tab {
            padding: 10px 20px;
            border: none;
            background: #f0f0f0;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.95rem;
            transition: all 0.3s;
            position: relative;
        }
        
        .tab:hover { background: #e0e0e0; transform: translateY(-1px); }
        .tab.active { background: #667eea; color: white; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .tab.active::after { content: ''; position: absolute; bottom: -2px; left: 50%; transform: translateX(-50%); width: 20px; height: 3px; background: #5a6fd6; border-radius: 2px; }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        select, input, button {
            padding: 12px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }
        
        select:focus, input:focus { border-color: #667eea; }
        
        button {
            background: #667eea;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        
        button:hover { background: #5a6fd6; }
        
        .ideas {
            display: grid;
            gap: 15px;
        }
        
        .idea {
            background: #f8f9ff;
            padding: 18px;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }
        
        .idea h3 {
            color: #667eea;
            margin-bottom: 8px;
            font-size: 1.1rem;
        }
        
        .idea p {
            color: #555;
            line-height: 1.5;
        }
        
        .idea .meta {
            margin-top: 10px;
            font-size: 0.85rem;
            color: #888;
        }
        
        .tag {
            display: inline-block;
            background: #e8eaff;
            color: #667eea;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-right: 8px;
        }
        
        .activity-detail {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-top: 15px;
            border: 2px solid #e8eaff;
        }
        
        .activity-detail h4 {
            color: #667eea;
            font-size: 1.2rem;
            margin-bottom: 10px;
        }
        
        .activity-detail .materials {
            background: #fff9e6;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 3px solid #ffc107;
        }
        
        .activity-detail .skills {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        
        .skill-tag {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
        }
        
        footer {
            text-align: center;
            color: white;
            opacity: 0.7;
            margin-top: 30px;
            padding: 20px;
        }
        
        @media (max-width: 600px) {
            header h1 { font-size: 1.8rem; }
            .controls { flex-direction: column; }
            select, input, button { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎨 Kindergarten Teacher Tools</h1>
            <p>Worksheets & Indoor Activity Ideas for a Kindergarten class</p>
        </header>
        
        <div class="card">
            <h2>📝 Worksheet Generator</h2>
            <div class="tabs" id="worksheet-tabs">
                <button class="tab active" onclick="setWorksheetCategory('letters')">🔤 Letters</button>
                <button class="tab" onclick="setWorksheetCategory('numbers')">🔢 Numbers</button>
                <button class="tab" onclick="setWorksheetCategory('shapes')">⭐ Shapes</button>
                <button class="tab" onclick="setWorksheetCategory('colors')">🎨 Colors</button>
                <button class="tab" onclick="setWorksheetCategory('mazes')">🧩 Mazes</button>
                <button class="tab" onclick="setWorksheetCategory('coloring')">🖍️ Coloring</button>
            </div>
            <div class="controls">
                <select id="ws-difficulty">
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                </select>
                <select id="ws-count">
                    <option value="3">3 Ideas</option>
                    <option value="5" selected>5 Ideas</option>
                    <option value="10">10 Ideas</option>
                </select>
                <button onclick="generateWorksheets()">✨ Generate Ideas</button>
            </div>
            <div id="worksheet-ideas" class="ideas">
                <div class="idea">
                    <p style="color: #888; text-align: center;">Click "Generate Ideas" to see worksheet suggestions!</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🎮 Indoor Activity Generator</h2>
            <div class="tabs" id="activity-tabs">
                <button class="tab active" onclick="setActivityCategory('indoor')">🏃 Active</button>
                <button class="tab" onclick="setActivityCategory('creative')">🎨 Creative</button>
                <button class="tab" onclick="setActivityCategory('movement')">💪 Movement</button>
                <button class="tab" onclick="setActivityCategory('calm')">😌 Calm</button>
                <button class="tab" onclick="setActivityCategory('social')">👫 Social</button>
            </div>
            <div class="controls">
                <select id="act-duration">
                    <option value="10">Up to 10 min</option>
                    <option value="15" selected">Up to 15 min</option>
                    <option value="20">Up to 20 min</option>
                    <option value="30">Up to 30 min</option>
                </select>
                <select id="act-count">
                    <option value="3" selected>3 Activities</option>
                    <option value="5">5 Activities</option>
                </select>
                <button onclick="generateActivities()">✨ Generate Activities</button>
            </div>
            <div id="activity-ideas" class="ideas">
                <div class="idea">
                    <p style="color: #888; text-align: center;">Click "Generate Activities" to see activity suggestions!</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🎲 Random Idea Generator</h2>
            <div class="controls">
                <select id="random-type">
                    <option value="worksheet">Worksheet</option>
                    <option value="activity">Activity</option>
                </select>
                <select id="random-count">
                    <option value="3" selected>3 Ideas</option>
                    <option value="5">5 Ideas</option>
                </select>
                <button onclick="generateRandom()">🎲 Surprise Me!</button>
            </div>
            <div id="random-ideas" class="ideas"></div>
        </div>
        
        <footer>
            <p>Built for Kindergarten Classroom ❤️ | Kindergarten Teacher Tools v1.0</p>
        </footer>
    </div>
    
    <script>
        let currentWsCategory = 'letters';
        let currentActCategory = 'indoor';
        
        function setWorksheetCategory(cat) {
            currentWsCategory = cat;
            const tabs = document.querySelectorAll('#worksheet-tabs .tab');
            const cats = ['letters', 'numbers', 'shapes', 'colors', 'mazes', 'coloring'];
            tabs.forEach((t, i) => t.classList.toggle('active', cats[i] === cat));
        }
        
        function setActivityCategory(cat) {
            currentActCategory = cat;
            const tabs = document.querySelectorAll('#activity-tabs .tab');
            const cats = ['indoor', 'creative', 'movement', 'calm', 'social'];
            tabs.forEach((t, i) => t.classList.toggle('active', cats[i] === cat));
        }
        
        async function generateWorksheets() {
            const difficulty = document.getElementById('ws-difficulty').value;
            const count = document.getElementById('ws-count').value;
            const container = document.getElementById('worksheet-ideas');
            
            container.innerHTML = '<div class="idea"><p>Loading...</p></div>';
            
            try {
                const res = await fetch(`/api/worksheets?category=${currentWsCategory}&difficulty=${difficulty}&count=${count}`);
                const data = await res.json();
                
                container.innerHTML = data.ideas.map((idea, idx) => {
                    const safeIdea = idea.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                    return `
                    <div class="idea" style="display: flex; justify-content: space-between; align-items: flex-start; gap: 15px;">
                        <div style="flex: 1;">
                            <span class="tag">${currentWsCategory}</span>
                            <span class="tag">${difficulty}</span>
                            <p>${idea}</p>
                        </div>
                        <button class="pdf-btn" data-idea="${safeIdea}" data-category="${currentWsCategory}" data-difficulty="${difficulty}" style="white-space: nowrap; margin-top: 0;">📄 Generate PDF</button>
                    </div>
                `}).join('');
                
                // Add event listeners to all PDF buttons
                document.querySelectorAll('.pdf-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        generateWorksheetPDF(
                            this.getAttribute('data-idea'),
                            this.getAttribute('data-category'),
                            this.getAttribute('data-difficulty')
                        );
                    });
                });
            } catch (e) {
                container.innerHTML = '<div class="idea"><p>Error loading ideas. Please try again.</p></div>';
            }
        }
        
        async function generateWorksheetPDF(idea, category, difficulty) {
            try {
                console.log('Generating PDF for:', idea, category, difficulty);
                
                const formData = new FormData();
                formData.append('idea', idea);
                formData.append('category', category);
                formData.append('difficulty', difficulty);
                
                console.log('Sending FormData...');
                const response = await fetch('/api/generate-worksheet-pdf', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    const text = await response.text();
                    console.error('Error response:', text);
                    throw new Error(`HTTP ${response.status}: ${text}`);
                }
                
                const blob = await response.blob();
                console.log('Blob received, size:', blob.size);
                
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `worksheet_${category}_${difficulty}.pdf`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
                
                console.log('PDF downloaded successfully');
            } catch (e) {
                console.error('Error:', e);
                alert('Error generating PDF: ' + e.message);
            }
        }
        
        async function generateActivities() {
            const duration = document.getElementById('act-duration').value;
            const count = document.getElementById('act-count').value;
            const container = document.getElementById('activity-ideas');
            
            container.innerHTML = '<div class="idea"><p>Loading...</p></div>';
            
            try {
                const res = await fetch(`/api/activities?category=${currentActCategory}&count=${count}&duration_minutes=${duration}`);
                const data = await res.json();
                
                container.innerHTML = data.activities.map(act => `
                    <div class="idea">
                        <div class="activity-detail">
                            <img src="/api/activity-image?activity=${encodeURIComponent(act.name)}" alt="${act.name}" style="max-width: 200px; border: 2px solid #667eea; border-radius: 10px; margin-bottom: 10px;">
                            <h4>${act.name}</h4>
                            <p>${act.description}</p>
                            <div class="materials"><strong>📦 Materials:</strong> ${act.materials}</div>
                            <div class="skills">
                                ${act.skills.map(s => `<span class="skill-tag">${s}</span>`).join('')}
                            </div>
                            <div class="meta">⏱️ ~${act.duration_min} minutes</div>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                container.innerHTML = '<div class="idea"><p>Error loading activities. Please try again.</p></div>';
            }
        }
        
        async function generateRandom() {
            const type = document.getElementById('random-type').value;
            const count = document.getElementById('random-count').value;
            const container = document.getElementById('random-ideas');
            
            container.innerHTML = '<div class="idea"><p>Loading...</p></div>';
            
            try {
                const res = await fetch(`/api/ideas?type=${type}&count=${count}`);
                const data = await res.json();
                
                if (type === 'worksheet') {
                    container.innerHTML = data.ideas.map(idea => `
                        <div class="idea">
                            <span class="tag">${data.category}</span>
                            <span class="tag">${data.difficulty}</span>
                            <p>${idea}</p>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = data.activities.map(act => `
                        <div class="idea">
                            <div class="activity-detail">
                                <img src="/api/activity-image?activity=${encodeURIComponent(act.name)}" alt="${act.name}" style="max-width: 200px; border: 2px solid #667eea; border-radius: 10px; margin-bottom: 10px;">
                                <h4>${act.name}</h4>
                                <p>${act.description}</p>
                                <div class="meta">⏱️ ~${act.duration_min} minutes</div>
                            </div>
                        </div>
                    `).join('');
                }
            } catch (e) {
                container.innerHTML = '<div class="idea"><p>Error loading ideas. Please try again.</p></div>';
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
