"""
extract_compliance_components.py
---------------------------------
Extract meaningful compliance components from architectural vector PDFs.

This script identifies components that a building plan compliance associate
would review, rather than just raw text and geometry.

Usage:
    python3 scripts/extract_compliance_components.py --pdf path/to/plan.pdf

Output:
    - *_components.json: Structured compliance components
    - *_output.json: Raw extraction data (for debugging)
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

import pdfplumber
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union
from tqdm import tqdm

# =============================================================================
# Component Data Models
# =============================================================================

@dataclass
class Dimension:
    """Represents a dimensional measurement."""
    value: float  # in feet
    original_text: str
    location: Tuple[float, float]  # (x, y)
    unit: str = "ft"

    def to_dict(self):
        return asdict(self)


@dataclass
class Room:
    """Represents a room or space."""
    name: str
    room_type: str  # bedroom, bathroom, kitchen, etc.
    area: Optional[float] = None  # square feet
    dimensions: List[Dimension] = None
    width: Optional[float] = None
    length: Optional[float] = None
    location: Optional[Tuple[float, float]] = None
    boundary_polygon: Optional[Dict] = None

    def __post_init__(self):
        if self.dimensions is None:
            self.dimensions = []

    def to_dict(self):
        return {
            "name": self.name,
            "room_type": self.room_type,
            "area": self.area,
            "width": self.width,
            "length": self.length,
            "location": self.location,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "boundary_polygon": self.boundary_polygon
        }


@dataclass
class Setback:
    """Represents a setback measurement from property boundary."""
    direction: str  # front, rear, left_side, right_side
    distance: float  # in feet
    measured_from: str  # property_line, street, etc.
    location: Optional[Tuple[float, float]] = None
    dimension_text: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Opening:
    """Represents doors, windows, or other openings."""
    opening_type: str  # door, window, opening
    width: Optional[float] = None
    height: Optional[float] = None
    location: Optional[Tuple[float, float]] = None
    adjacent_room: Optional[str] = None
    is_egress: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class ParkingSpace:
    """Represents a parking space or garage."""
    space_type: str  # garage, carport, open_space
    width: Optional[float] = None
    length: Optional[float] = None
    count: int = 1
    location: Optional[Tuple[float, float]] = None
    accessible: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class Stair:
    """Represents stairs, ramps, or vertical circulation."""
    circulation_type: str  # stair, ramp, elevator, escalator
    width: Optional[float] = None
    rise: Optional[float] = None  # for stairs
    run: Optional[float] = None   # for stairs
    slope: Optional[float] = None  # for ramps (in degrees or ratio)
    num_treads: Optional[int] = None
    has_handrail: bool = False
    is_egress: bool = False
    location: Optional[Tuple[float, float]] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class FireSafety:
    """Represents fire safety components."""
    feature_type: str  # smoke_alarm, sprinkler, fire_exit, fire_door, hydrant, extinguisher
    location: Optional[Tuple[float, float]] = None
    coverage_area: Optional[float] = None
    rating: Optional[str] = None  # fire rating (e.g., "1HR", "2HR")

    def to_dict(self):
        return asdict(self)


@dataclass
class AccessibilityFeature:
    """Represents accessibility/ADA compliance features."""
    feature_type: str  # accessible_parking, ramp, accessible_entrance, accessible_bathroom
    compliant: Optional[bool] = None
    location: Optional[Tuple[float, float]] = None
    slope: Optional[float] = None  # for ramps
    clear_width: Optional[float] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class HeightLevel:
    """Represents height and level information."""
    level_name: str  # "Floor 1", "Ceiling", "Roof", etc.
    elevation: Optional[float] = None  # in feet
    height_above_grade: Optional[float] = None
    location: Optional[Tuple[float, float]] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class BuildingEnvelope:
    """Overall building dimensions and envelope."""
    total_width: Optional[float] = None
    total_length: Optional[float] = None
    total_height: Optional[float] = None
    floor_area: Optional[float] = None
    num_stories: Optional[int] = None
    roof_type: Optional[str] = None
    roof_pitch: Optional[float] = None  # in degrees
    perimeter: Optional[float] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class GeometricSetback:
    """Setback calculated from geometric analysis of boundaries."""
    direction: str
    min_distance: float
    max_distance: float
    avg_distance: float
    measurement_points: List[Tuple[float, float]]

    def __post_init__(self):
        if self.measurement_points is None:
            self.measurement_points = []

    def to_dict(self):
        return {
            "direction": self.direction,
            "min_distance": self.min_distance,
            "max_distance": self.max_distance,
            "avg_distance": self.avg_distance,
            "num_measurement_points": len(self.measurement_points)
        }


# =============================================================================
# Site Plan Data Models
# =============================================================================

@dataclass
class LotInfo:
    """Represents lot/parcel information for site plans."""
    lot_number: Optional[str] = None
    lot_area: Optional[float] = None  # in square meters or square feet
    lot_area_unit: str = "m²"  # or "ft²"
    boundary_dimensions: List[Dimension] = None  # perimeter dimensions
    street_frontage: Optional[str] = None
    boundary_polygon: Optional[Dict] = None
    location: Optional[Tuple[float, float]] = None

    def __post_init__(self):
        if self.boundary_dimensions is None:
            self.boundary_dimensions = []

    def to_dict(self):
        return {
            "lot_number": self.lot_number,
            "lot_area": self.lot_area,
            "lot_area_unit": self.lot_area_unit,
            "boundary_dimensions": [d.to_dict() for d in self.boundary_dimensions],
            "street_frontage": self.street_frontage,
            "boundary_polygon": self.boundary_polygon,
            "location": self.location
        }


@dataclass
class AdjacentProperty:
    """Represents adjacent lots/properties."""
    identifier: str  # e.g., "Lot 137", "SP163257"
    direction: Optional[str] = None  # north, south, east, west, front, rear
    location: Optional[Tuple[float, float]] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class WaterFeature:
    """Represents water features like creeks, rivers, ponds."""
    feature_type: str  # creek, river, pond, lake, stream, drainage
    name: Optional[str] = None
    location: Optional[Tuple[float, float]] = None
    boundary_relation: Optional[str] = None  # e.g., "rear boundary", "east side"

    def to_dict(self):
        return asdict(self)


@dataclass
class NorthPointer:
    """Represents north pointer/compass rose on site plans."""
    found: bool
    location: Optional[Tuple[float, float]] = None
    rotation: Optional[float] = None  # degrees from vertical
    pointer_type: str = "compass_rose"  # compass_rose, arrow, symbol

    def to_dict(self):
        return asdict(self)


@dataclass
class ComplianceComponents:
    """Container for all extracted compliance components."""
    sheet_number: int
    sheet_title: Optional[str]
    scale: Optional[str]
    rooms: List[Room]
    setbacks: List[Setback]
    geometric_setbacks: List[GeometricSetback]
    openings: List[Opening]
    parking: List[ParkingSpace]
    stairs: List[Stair]
    fire_safety: List[FireSafety]
    accessibility: List[AccessibilityFeature]
    height_levels: List[HeightLevel]
    building_envelope: Optional[BuildingEnvelope]
    dimensions_found: List[Dimension]
    annotations: List[str]
    # Site plan components
    lot_info: Optional[LotInfo] = None
    adjacent_properties: List[AdjacentProperty] = None
    water_features: List[WaterFeature] = None
    north_pointer: Optional[NorthPointer] = None

    def __post_init__(self):
        if self.rooms is None:
            self.rooms = []
        if self.setbacks is None:
            self.setbacks = []
        if self.geometric_setbacks is None:
            self.geometric_setbacks = []
        if self.openings is None:
            self.openings = []
        if self.parking is None:
            self.parking = []
        if self.stairs is None:
            self.stairs = []
        if self.fire_safety is None:
            self.fire_safety = []
        if self.accessibility is None:
            self.accessibility = []
        if self.height_levels is None:
            self.height_levels = []
        if self.dimensions_found is None:
            self.dimensions_found = []
        if self.annotations is None:
            self.annotations = []
        if self.adjacent_properties is None:
            self.adjacent_properties = []
        if self.water_features is None:
            self.water_features = []

    def to_dict(self):
        return {
            "sheet_number": self.sheet_number,
            "sheet_title": self.sheet_title,
            "scale": self.scale,
            "rooms": [r.to_dict() for r in self.rooms],
            "setbacks": [s.to_dict() for s in self.setbacks],
            "geometric_setbacks": [gs.to_dict() for gs in self.geometric_setbacks],
            "openings": [o.to_dict() for o in self.openings],
            "parking": [p.to_dict() for p in self.parking],
            "stairs": [s.to_dict() for s in self.stairs],
            "fire_safety": [f.to_dict() for f in self.fire_safety],
            "accessibility": [a.to_dict() for a in self.accessibility],
            "height_levels": [h.to_dict() for h in self.height_levels],
            "building_envelope": self.building_envelope.to_dict() if self.building_envelope else None,
            "dimensions_found": [d.to_dict() for d in self.dimensions_found],
            "annotations": self.annotations,
            # Site plan components
            "lot_info": self.lot_info.to_dict() if self.lot_info else None,
            "adjacent_properties": [ap.to_dict() for ap in self.adjacent_properties],
            "water_features": [wf.to_dict() for wf in self.water_features],
            "north_pointer": self.north_pointer.to_dict() if self.north_pointer else None
        }


# =============================================================================
# Extraction Patterns & Keywords
# =============================================================================

# Room type keywords
ROOM_KEYWORDS = {
    "bedroom": ["BEDROOM", "BED", "BR", "MASTER", "GUEST ROOM"],
    "bathroom": ["BATH", "TOILET", "WC", "SHOWER", "ENSUITE", "POWDER"],
    "kitchen": ["KITCHEN", "PANTRY", "COOK"],
    "living": ["LIVING", "LOUNGE", "FAMILY", "GREAT ROOM"],
    "dining": ["DINING", "MEALS", "BREAKFAST", "NOOK"],
    "garage": ["GARAGE", "CARPORT", "CAR SPACE"],
    "laundry": ["LAUNDRY", "UTILITY", "MUD ROOM"],
    "entry": ["ENTRY", "FOYER", "VESTIBULE", "HALL"],
    "balcony": ["BALCONY", "DECK", "PORCH", "PATIO", "TERRACE"],
    "storage": ["STORAGE", "CLOSET", "WARDROBE", "LINEN"],
}

# Setback/boundary keywords
SETBACK_KEYWORDS = [
    "SETBACK", "BOUNDARY", "PROPERTY LINE", "LOT LINE",
    "EASEMENT", "RIGHT OF WAY", "ROW"
]

# Opening keywords
DOOR_KEYWORDS = ["DOOR", "ENTRY", "EXIT"]
WINDOW_KEYWORDS = ["WINDOW", "GLAZING"]

# Parking keywords
PARKING_KEYWORDS = ["PARKING", "GARAGE", "CARPORT", "CAR SPACE", "DRIVEWAY"]

# Stair/circulation keywords
STAIR_KEYWORDS = ["STAIR", "STEP", "RISER", "TREAD", "UP", "DOWN", "DN"]
RAMP_KEYWORDS = ["RAMP", "SLOPE", "ACCESSIBLE RAMP", "ADA RAMP"]
ELEVATOR_KEYWORDS = ["ELEVATOR", "LIFT", "ELEV"]

# Fire safety keywords
FIRE_SAFETY_KEYWORDS = {
    "smoke_alarm": ["SMOKE ALARM", "SMOKE DETECTOR", "SD"],
    "sprinkler": ["SPRINKLER", "FIRE SPRINKLER", "SPK"],
    "fire_exit": ["FIRE EXIT", "EMERGENCY EXIT", "EXIT"],
    "fire_door": ["FIRE DOOR", "FD", "FIRE RATED"],
    "hydrant": ["HYDRANT", "FIRE HYDRANT", "FH"],
    "extinguisher": ["FIRE EXTINGUISHER", "EXTINGUISHER", "FE"]
}

# Accessibility keywords
ACCESSIBILITY_KEYWORDS = ["ACCESSIBLE", "ADA", "AS1428", "DISABILITY", "HANDICAP", "HC"]

# Height/level keywords
HEIGHT_KEYWORDS = ["HEIGHT", "CEILING HEIGHT", "CH", "FLOOR LEVEL", "FL", "RL", "ELEVATION", "ELEV"]
ROOF_KEYWORDS = ["ROOF", "RIDGE", "EAVE", "PITCH"]

# Dimension patterns (architectural notation)
DIMENSION_PATTERNS = [
    r"(\d+)'-(\d+)\"",           # 10'-6"
    r"(\d+)'",                    # 10'
    r"(\d+)\"",                   # 6"
    r"(\d+)'-(\d+)\s*(\d+)/(\d+)\"",  # 10'-6 1/2"
    r"(\d+\.\d+)'\s*",            # 10.5'
]

# Metric dimension patterns
METRIC_DIMENSION_PATTERNS = [
    r"(\d+\.?\d*)\s*m\b",         # 68.3m or 68m
    r"(\d+\.?\d*)\s*mm\b",        # 1000mm
    r"(\d+\.?\d*)\s*cm\b",        # 100cm
]

# Scale patterns
SCALE_PATTERNS = [
    r"SCALE:\s*(.*?)(?:\n|$)",
    r"(\d+/\d+)\"\s*=\s*(\d+)'-(\d+)\"",
    r"1:(\d+)",
]

# Site plan keywords
LOT_KEYWORDS = ["LOT", "PARCEL", "SITE", "PROPERTY"]
NORTH_KEYWORDS = ["NORTH", "N", "COMPASS", "ORIENTATION"]
WATER_FEATURE_KEYWORDS = {
    "creek": ["CREEK", "CRK"],
    "river": ["RIVER"],
    "pond": ["POND"],
    "lake": ["LAKE"],
    "stream": ["STREAM"],
    "drainage": ["DRAINAGE", "DRAIN", "SWALE"]
}
ADJACENT_LOT_PATTERNS = [
    r"LOT\s+(\d+)",               # LOT 137
    r"SP\s*(\d+)",                # SP163257
    r"DP\s*(\d+)",                # DP123456 (Deposited Plan)
]


# =============================================================================
# Utility Functions
# =============================================================================

def log(msg: str) -> None:
    print(f"[INFO] {msg}")


def parse_dimension(text: str) -> Optional[float]:
    """
    Convert architectural dimension string to decimal feet.
    Examples: "10'-6"" -> 10.5, "3'" -> 3.0, "6"" -> 0.5
    """
    text = text.strip()

    # Pattern: 10'-6"
    match = re.match(r"(\d+)'-(\d+)\"", text)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        return feet + inches / 12.0

    # Pattern: 10'-6 1/2"
    match = re.match(r"(\d+)'-(\d+)\s*(\d+)/(\d+)\"", text)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        numerator = int(match.group(3))
        denominator = int(match.group(4))
        return feet + (inches + numerator/denominator) / 12.0

    # Pattern: 10'
    match = re.match(r"(\d+)'", text)
    if match:
        return float(match.group(1))

    # Pattern: 6"
    match = re.match(r"(\d+)\"", text)
    if match:
        return int(match.group(1)) / 12.0

    # Pattern: 10.5'
    match = re.match(r"(\d+\.\d+)'", text)
    if match:
        return float(match.group(1))

    return None


def extract_text_blocks(page) -> List[Dict]:
    """Extract text blocks with positions."""
    blocks = []
    for word in page.extract_words():
        blocks.append({
            "text": word["text"],
            "x0": word["x0"],
            "y0": word["top"],
            "x1": word["x1"],
            "y1": word["bottom"],
            "x": (word["x0"] + word["x1"]) / 2,
            "y": (word["top"] + word["bottom"]) / 2
        })
    return blocks


def find_nearby_text(target_block: Dict, all_blocks: List[Dict], radius: float = 50) -> List[Dict]:
    """Find text blocks near a target block."""
    target_point = Point(target_block["x"], target_block["y"])
    nearby = []
    for block in all_blocks:
        block_point = Point(block["x"], block["y"])
        if target_point.distance(block_point) <= radius:
            nearby.append(block)
    return nearby


# =============================================================================
# Component Extractors
# =============================================================================

class ComponentExtractor:
    """Main class for extracting compliance components from PDF pages."""

    def __init__(self, page, page_number: int):
        self.page = page
        self.page_number = page_number
        self.text_blocks = extract_text_blocks(page)
        self.all_text_upper = " ".join([b["text"] for b in self.text_blocks]).upper()

    def extract_scale(self) -> Optional[str]:
        """Extract the drawing scale."""
        for block in self.text_blocks:
            if "SCALE" in block["text"].upper():
                # Look for nearby text
                nearby = find_nearby_text(block, self.text_blocks, radius=100)
                scale_text = " ".join([b["text"] for b in nearby])
                for pattern in SCALE_PATTERNS:
                    match = re.search(pattern, scale_text, re.IGNORECASE)
                    if match:
                        return match.group(0)
        return None

    def extract_sheet_title(self) -> Optional[str]:
        """Extract sheet title (usually at top of page)."""
        title_keywords = ["FLOOR PLAN", "SITE PLAN", "ELEVATION", "SECTION", "FOUNDATION"]
        for block in self.text_blocks:
            text_upper = block["text"].upper()
            if any(kw in text_upper for kw in title_keywords):
                # Get nearby text to build full title
                nearby = find_nearby_text(block, self.text_blocks, radius=150)
                title = " ".join([b["text"] for b in sorted(nearby, key=lambda x: x["x"])])
                return title[:100]  # Limit length
        return None

    def extract_dimensions(self) -> List[Dimension]:
        """Extract all dimension annotations."""
        dimensions = []
        for block in self.text_blocks:
            for pattern in DIMENSION_PATTERNS:
                if re.match(pattern, block["text"]):
                    value = parse_dimension(block["text"])
                    if value:
                        dim = Dimension(
                            value=value,
                            original_text=block["text"],
                            location=(block["x"], block["y"]),
                            unit="ft"
                        )
                        dimensions.append(dim)
                    break
        return dimensions

    def extract_rooms(self) -> List[Room]:
        """Extract room information."""
        rooms = []
        found_room_names = set()

        for room_type, keywords in ROOM_KEYWORDS.items():
            for block in self.text_blocks:
                text_upper = block["text"].upper()

                # Check if this block matches room keywords
                matched_keyword = None
                for kw in keywords:
                    if kw in text_upper:
                        matched_keyword = kw
                        break

                if matched_keyword:
                    # Avoid duplicates
                    room_key = f"{room_type}_{block['x']:.0f}_{block['y']:.0f}"
                    if room_key in found_room_names:
                        continue
                    found_room_names.add(room_key)

                    # Find nearby dimensions
                    nearby_blocks = find_nearby_text(block, self.text_blocks, radius=100)
                    room_dims = []
                    for nearby in nearby_blocks:
                        dim_value = parse_dimension(nearby["text"])
                        if dim_value:
                            room_dims.append(Dimension(
                                value=dim_value,
                                original_text=nearby["text"],
                                location=(nearby["x"], nearby["y"])
                            ))

                    # Calculate area if we have 2 dimensions
                    area = None
                    width = None
                    length = None
                    if len(room_dims) >= 2:
                        width = room_dims[0].value
                        length = room_dims[1].value
                        area = width * length

                    room = Room(
                        name=block["text"],
                        room_type=room_type,
                        area=area,
                        width=width,
                        length=length,
                        location=(block["x"], block["y"]),
                        dimensions=room_dims
                    )
                    rooms.append(room)

        return rooms

    def extract_setbacks(self) -> List[Setback]:
        """Extract setback measurements."""
        setbacks = []

        for block in self.text_blocks:
            text_upper = block["text"].upper()

            # Check for setback keywords
            is_setback = any(kw in text_upper for kw in SETBACK_KEYWORDS)
            if not is_setback:
                continue

            # Find nearby dimensions
            nearby_blocks = find_nearby_text(block, self.text_blocks, radius=150)
            for nearby in nearby_blocks:
                dim_value = parse_dimension(nearby["text"])
                if dim_value:
                    # Determine direction from context
                    direction = "unknown"
                    context_text = " ".join([b["text"].upper() for b in nearby_blocks])
                    if "FRONT" in context_text:
                        direction = "front"
                    elif "REAR" in context_text or "BACK" in context_text:
                        direction = "rear"
                    elif "SIDE" in context_text:
                        if "LEFT" in context_text:
                            direction = "left_side"
                        elif "RIGHT" in context_text:
                            direction = "right_side"
                        else:
                            direction = "side"

                    setback = Setback(
                        direction=direction,
                        distance=dim_value,
                        measured_from="property_line",
                        location=(block["x"], block["y"]),
                        dimension_text=nearby["text"]
                    )
                    setbacks.append(setback)

        return setbacks

    def extract_openings(self) -> List[Opening]:
        """Extract doors and windows."""
        openings = []

        # Check for door keywords
        for block in self.text_blocks:
            text_upper = block["text"].upper()

            opening_type = None
            if any(kw in text_upper for kw in DOOR_KEYWORDS):
                opening_type = "door"
            elif any(kw in text_upper for kw in WINDOW_KEYWORDS):
                opening_type = "window"

            if opening_type:
                # Find dimensions nearby
                nearby = find_nearby_text(block, self.text_blocks, radius=80)
                dims = [parse_dimension(b["text"]) for b in nearby]
                dims = [d for d in dims if d is not None]

                width = dims[0] if len(dims) > 0 else None
                height = dims[1] if len(dims) > 1 else None

                opening = Opening(
                    opening_type=opening_type,
                    width=width,
                    height=height,
                    location=(block["x"], block["y"]),
                    is_egress="EXIT" in text_upper or "EGRESS" in text_upper
                )
                openings.append(opening)

        return openings

    def extract_parking(self) -> List[ParkingSpace]:
        """Extract parking spaces and garages."""
        parking = []

        for block in self.text_blocks:
            text_upper = block["text"].upper()

            if any(kw in text_upper for kw in PARKING_KEYWORDS):
                # Determine type
                space_type = "open_space"
                if "GARAGE" in text_upper:
                    space_type = "garage"
                elif "CARPORT" in text_upper:
                    space_type = "carport"

                # Find dimensions
                nearby = find_nearby_text(block, self.text_blocks, radius=100)
                dims = [parse_dimension(b["text"]) for b in nearby]
                dims = [d for d in dims if d is not None]

                width = dims[0] if len(dims) > 0 else None
                length = dims[1] if len(dims) > 1 else None

                parking_space = ParkingSpace(
                    space_type=space_type,
                    width=width,
                    length=length,
                    location=(block["x"], block["y"]),
                    accessible="ACCESSIBLE" in text_upper or "ADA" in text_upper
                )
                parking.append(parking_space)

        return parking

    def extract_stairs(self) -> List[Stair]:
        """Extract stairs, ramps, and vertical circulation."""
        stairs = []

        for block in self.text_blocks:
            text_upper = block["text"].upper()

            circulation_type = None
            if any(kw in text_upper for kw in STAIR_KEYWORDS):
                circulation_type = "stair"
            elif any(kw in text_upper for kw in RAMP_KEYWORDS):
                circulation_type = "ramp"
            elif any(kw in text_upper for kw in ELEVATOR_KEYWORDS):
                circulation_type = "elevator"

            if circulation_type:
                nearby = find_nearby_text(block, self.text_blocks, radius=100)
                context_text = " ".join([b["text"].upper() for b in nearby])

                # Extract dimensions
                dims = [parse_dimension(b["text"]) for b in nearby]
                dims = [d for d in dims if d is not None]

                width = dims[0] if len(dims) > 0 else None

                # For ramps, look for slope
                slope = None
                if circulation_type == "ramp":
                    # Look for slope ratio or percentage
                    slope_match = re.search(r"(\d+):(\d+)", context_text)
                    if slope_match:
                        slope = float(slope_match.group(1)) / float(slope_match.group(2))
                    else:
                        pct_match = re.search(r"(\d+)%", context_text)
                        if pct_match:
                            slope = float(pct_match.group(1)) / 100.0

                stair = Stair(
                    circulation_type=circulation_type,
                    width=width,
                    slope=slope,
                    is_egress="EXIT" in context_text or "EGRESS" in context_text,
                    has_handrail="HANDRAIL" in context_text or "RAIL" in context_text,
                    location=(block["x"], block["y"])
                )
                stairs.append(stair)

        return stairs

    def extract_fire_safety(self) -> List[FireSafety]:
        """Extract fire safety components."""
        fire_safety = []

        for feature_type, keywords in FIRE_SAFETY_KEYWORDS.items():
            for block in self.text_blocks:
                text_upper = block["text"].upper()

                if any(kw in text_upper for kw in keywords):
                    nearby = find_nearby_text(block, self.text_blocks, radius=80)
                    context_text = " ".join([b["text"].upper() for b in nearby])

                    # Look for fire rating
                    rating = None
                    rating_match = re.search(r"(\d+)\s*HR", context_text)
                    if rating_match:
                        rating = f"{rating_match.group(1)}HR"

                    feature = FireSafety(
                        feature_type=feature_type,
                        location=(block["x"], block["y"]),
                        rating=rating
                    )
                    fire_safety.append(feature)

        return fire_safety

    def extract_accessibility(self) -> List[AccessibilityFeature]:
        """Extract accessibility/ADA features."""
        accessibility = []

        for block in self.text_blocks:
            text_upper = block["text"].upper()

            if any(kw in text_upper for kw in ACCESSIBILITY_KEYWORDS):
                nearby = find_nearby_text(block, self.text_blocks, radius=100)
                context_text = " ".join([b["text"].upper() for b in nearby])

                # Determine feature type from context
                feature_type = "accessible_feature"
                if "PARKING" in context_text or "PARK" in context_text:
                    feature_type = "accessible_parking"
                elif "RAMP" in context_text:
                    feature_type = "accessible_ramp"
                elif "ENTRANCE" in context_text or "ENTRY" in context_text:
                    feature_type = "accessible_entrance"
                elif "BATH" in context_text or "TOILET" in context_text:
                    feature_type = "accessible_bathroom"

                # Extract dimensions
                dims = [parse_dimension(b["text"]) for b in nearby]
                dims = [d for d in dims if d is not None]
                clear_width = dims[0] if len(dims) > 0 else None

                # Look for slope (for ramps)
                slope = None
                slope_match = re.search(r"(\d+):(\d+)", context_text)
                if slope_match:
                    slope = float(slope_match.group(1)) / float(slope_match.group(2))

                feature = AccessibilityFeature(
                    feature_type=feature_type,
                    location=(block["x"], block["y"]),
                    clear_width=clear_width,
                    slope=slope,
                    compliant="COMPLIANT" in context_text or "ADA" in context_text
                )
                accessibility.append(feature)

        return accessibility

    def extract_height_levels(self) -> List[HeightLevel]:
        """Extract height and level information."""
        height_levels = []

        for block in self.text_blocks:
            text_upper = block["text"].upper()

            if any(kw in text_upper for kw in HEIGHT_KEYWORDS + ROOF_KEYWORDS):
                nearby = find_nearby_text(block, self.text_blocks, radius=100)

                # Extract elevation value
                dims = [parse_dimension(b["text"]) for b in nearby]
                dims = [d for d in dims if d is not None]
                elevation = dims[0] if len(dims) > 0 else None

                # Determine level name
                level_name = block["text"]

                level = HeightLevel(
                    level_name=level_name,
                    elevation=elevation,
                    location=(block["x"], block["y"])
                )
                height_levels.append(level)

        return height_levels

    def extract_geometric_setbacks(self) -> List[GeometricSetback]:
        """Calculate setbacks from geometric analysis of building and property boundaries."""
        geometric_setbacks = []

        try:
            # Extract all rectangles (building footprint and property boundaries)
            rects = self.page.rects
            if not rects or len(rects) < 2:
                return geometric_setbacks

            # Find largest rectangle (likely property boundary)
            rects_with_area = []
            for rect in rects:
                width = abs(rect["x1"] - rect["x0"])
                height = abs(rect["y1"] - rect["y0"])
                area = width * height
                if area > 100:  # Filter out small decorative elements
                    rects_with_area.append((rect, area))

            if len(rects_with_area) < 2:
                return geometric_setbacks

            # Sort by area - largest is property, second largest is building
            rects_with_area.sort(key=lambda x: x[1], reverse=True)
            property_rect = rects_with_area[0][0]
            building_rect = rects_with_area[1][0]

            # Calculate setbacks for each direction
            # Front (assuming top of page is front)
            front_setback = abs(building_rect["y0"] - property_rect["y0"])
            # Rear
            rear_setback = abs(property_rect["y1"] - building_rect["y1"])
            # Left side
            left_setback = abs(building_rect["x0"] - property_rect["x0"])
            # Right side
            right_setback = abs(property_rect["x1"] - building_rect["x1"])

            # Convert from PDF points to feet (if scale is available)
            # For now, just use relative measurements
            # TODO: Use actual scale conversion

            if front_setback > 1:
                geometric_setbacks.append(GeometricSetback(
                    direction="front",
                    min_distance=front_setback,
                    max_distance=front_setback,
                    avg_distance=front_setback,
                    measurement_points=[(building_rect["x0"], building_rect["y0"])]
                ))

            if rear_setback > 1:
                geometric_setbacks.append(GeometricSetback(
                    direction="rear",
                    min_distance=rear_setback,
                    max_distance=rear_setback,
                    avg_distance=rear_setback,
                    measurement_points=[(building_rect["x1"], building_rect["y1"])]
                ))

            if left_setback > 1:
                geometric_setbacks.append(GeometricSetback(
                    direction="left_side",
                    min_distance=left_setback,
                    max_distance=left_setback,
                    avg_distance=left_setback,
                    measurement_points=[(building_rect["x0"], building_rect["y0"])]
                ))

            if right_setback > 1:
                geometric_setbacks.append(GeometricSetback(
                    direction="right_side",
                    min_distance=right_setback,
                    max_distance=right_setback,
                    avg_distance=right_setback,
                    measurement_points=[(building_rect["x1"], building_rect["y1"])]
                ))

        except Exception as e:
            log(f"Warning: Could not calculate geometric setbacks: {e}")

        return geometric_setbacks

    def extract_building_envelope(self, dimensions: List[Dimension]) -> Optional[BuildingEnvelope]:
        """Extract overall building dimensions."""
        # Look for "overall" dimension
        overall_dims = []
        for block in self.text_blocks:
            if "OVERALL" in block["text"].upper():
                nearby = find_nearby_text(block, self.text_blocks, radius=100)
                for n in nearby:
                    dim_val = parse_dimension(n["text"])
                    if dim_val:
                        overall_dims.append(dim_val)

        # Sort dimensions to get width/length
        if len(overall_dims) >= 2:
            overall_dims.sort(reverse=True)

            # Calculate perimeter
            perimeter = 2 * (overall_dims[0] + overall_dims[1])

            envelope = BuildingEnvelope(
                total_length=overall_dims[0],
                total_width=overall_dims[1],
                floor_area=overall_dims[0] * overall_dims[1],
                perimeter=perimeter
            )
            return envelope

        return None

    # =========================================================================
    # Site Plan Extraction Methods
    # =========================================================================

    def extract_lot_info(self) -> Optional[LotInfo]:
        """Extract lot/parcel information from site plans."""
        lot_info = LotInfo()

        # Extract lot number
        for block in self.text_blocks:
            text_upper = block["text"].upper()
            # Look for "LOT" followed by a number in same block
            lot_match = re.search(r"LOT\s+(\d+)", text_upper)
            if lot_match:
                lot_info.lot_number = lot_match.group(1)
                lot_info.location = (block["x"], block["y"])
                break

            # Also check if "LOT" appears, then look nearby for number
            if text_upper.strip() == "LOT":
                nearby = find_nearby_text(block, self.text_blocks, radius=100)
                for n in nearby:
                    # Look for a number that could be lot number (1-3 digits typically)
                    num_match = re.search(r"^(\d{1,4})$", n["text"].strip())
                    if num_match:
                        lot_info.lot_number = num_match.group(1)
                        lot_info.location = (block["x"], block["y"])
                        break
                if lot_info.lot_number:
                    break

        # Extract lot area (look for area pattern like "1,190 m²" or "Area: 1,190")
        for block in self.text_blocks:
            text = block["text"]
            # Pattern: number with comma + m² or number + m²
            area_match = re.search(r"([\d,]+\.?\d*)\s*(?:m²|m2|sqm)", text, re.IGNORECASE)
            if area_match:
                area_str = area_match.group(1).replace(",", "")
                try:
                    lot_info.lot_area = float(area_str)
                    lot_info.lot_area_unit = "m²"
                    if not lot_info.location:
                        lot_info.location = (block["x"], block["y"])
                except ValueError:
                    pass

            # Also check for "Area:" label nearby
            if "AREA" in block["text"].upper():
                nearby = find_nearby_text(block, self.text_blocks, radius=150)
                for n in nearby:
                    # Look for numbers with commas (e.g., "1,190")
                    area_match = re.search(r"([\d,]+\.?\d*)", n["text"])
                    if area_match and not lot_info.lot_area:
                        try:
                            area_str = area_match.group(1).replace(",", "")
                            area_val = float(area_str)
                            # Reasonable lot size (not just any number)
                            if 100 < area_val < 100000:  # Between 100 and 100,000 sqm
                                lot_info.lot_area = area_val
                                lot_info.lot_area_unit = "m²"
                        except ValueError:
                            pass

            # Check if this block itself contains a large number (could be area without "Area:" label)
            if not lot_info.lot_area:
                num_match = re.search(r"([\d,]+)$", block["text"])
                if num_match:
                    try:
                        area_str = num_match.group(1).replace(",", "")
                        area_val = float(area_str)
                        if 500 < area_val < 100000:  # Large enough to be lot area
                            # Check if m² is nearby
                            nearby = find_nearby_text(block, self.text_blocks, radius=50)
                            nearby_text = " ".join([b["text"] for b in nearby])
                            if "m²" in nearby_text or "m2" in nearby_text or "sqm" in nearby_text.lower():
                                lot_info.lot_area = area_val
                                lot_info.lot_area_unit = "m²"
                                lot_info.location = (block["x"], block["y"])
                    except ValueError:
                        pass

        # Extract boundary dimensions (metric)
        # First try with explicit unit markers
        for block in self.text_blocks:
            for pattern in METRIC_DIMENSION_PATTERNS:
                match = re.search(pattern, block["text"])
                if match:
                    try:
                        value = float(match.group(1))
                        # Filter out very small or very large values
                        if 5 < value < 500:  # Reasonable range for lot dimensions in meters
                            dim = Dimension(
                                value=value,
                                original_text=block["text"],
                                location=(block["x"], block["y"]),
                                unit="m"
                            )
                            lot_info.boundary_dimensions.append(dim)
                    except (ValueError, IndexError):
                        pass

        # If no dimensions found with units, try bare numbers (common on site plans)
        if not lot_info.boundary_dimensions:
            for block in self.text_blocks:
                # Look for decimal numbers that could be dimensions (e.g., "68.3", "56.9")
                match = re.search(r"^(\d+\.?\d*)$", block["text"].strip())
                if match:
                    try:
                        value = float(match.group(1))
                        # Reasonable range for lot boundary dimensions
                        if 5 < value < 200:
                            dim = Dimension(
                                value=value,
                                original_text=block["text"],
                                location=(block["x"], block["y"]),
                                unit="m"  # Assume meters for site plans
                            )
                            lot_info.boundary_dimensions.append(dim)
                    except (ValueError, IndexError):
                        pass

        # Only return if we found meaningful data
        if lot_info.lot_number or lot_info.lot_area or lot_info.boundary_dimensions:
            return lot_info
        return None

    def extract_adjacent_properties(self) -> List[AdjacentProperty]:
        """Extract adjacent lot/property identifiers."""
        adjacent_props = []
        seen_identifiers = set()

        for block in self.text_blocks:
            text_upper = block["text"].upper()

            # Check each pattern
            for pattern in ADJACENT_LOT_PATTERNS:
                matches = re.finditer(pattern, text_upper)
                for match in matches:
                    identifier = match.group(0)
                    if identifier not in seen_identifiers:
                        seen_identifiers.add(identifier)
                        adjacent_props.append(
                            AdjacentProperty(
                                identifier=identifier,
                                location=(block["x"], block["y"])
                            )
                        )

        return adjacent_props

    def extract_water_features(self) -> List[WaterFeature]:
        """Extract water features like creeks, rivers, ponds."""
        water_features = []
        seen_features = set()

        for block in self.text_blocks:
            text_upper = block["text"].upper()

            for feature_type, keywords in WATER_FEATURE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text_upper:
                        # Get full name from nearby text
                        nearby = find_nearby_text(block, self.text_blocks, radius=150)
                        name_parts = [b["text"] for b in sorted(nearby, key=lambda x: x["x"])]
                        full_name = " ".join(name_parts[:3])  # Limit to avoid too much text

                        if full_name not in seen_features:
                            seen_features.add(full_name)
                            water_features.append(
                                WaterFeature(
                                    feature_type=feature_type,
                                    name=full_name,
                                    location=(block["x"], block["y"])
                                )
                            )

        return water_features

    def extract_north_pointer(self) -> Optional[NorthPointer]:
        """Detect north pointer/compass rose."""
        # Look for north indicators in text
        for block in self.text_blocks:
            text_upper = block["text"].upper()
            if any(kw in text_upper for kw in NORTH_KEYWORDS):
                # Check if it's a standalone "N" or "NORTH" (likely compass)
                if text_upper.strip() in ["N", "NORTH"]:
                    return NorthPointer(
                        found=True,
                        location=(block["x"], block["y"]),
                        pointer_type="text_indicator"
                    )

        # Could also check for circular/compass-like shapes in the geometry
        # but for now, just check text
        return NorthPointer(found=False)

    def extract_all(self) -> ComplianceComponents:
        """Extract all components from the page."""
        log(f"Extracting components from sheet {self.page_number}...")

        scale = self.extract_scale()
        sheet_title = self.extract_sheet_title()
        dimensions = self.extract_dimensions()
        rooms = self.extract_rooms()
        setbacks = self.extract_setbacks()
        geometric_setbacks = self.extract_geometric_setbacks()
        openings = self.extract_openings()
        parking = self.extract_parking()
        stairs = self.extract_stairs()
        fire_safety = self.extract_fire_safety()
        accessibility = self.extract_accessibility()
        height_levels = self.extract_height_levels()
        envelope = self.extract_building_envelope(dimensions)

        # Extract site plan components
        lot_info = self.extract_lot_info()
        adjacent_properties = self.extract_adjacent_properties()
        water_features = self.extract_water_features()
        north_pointer = self.extract_north_pointer()

        # Extract general annotations (non-dimension text)
        annotations = []
        annotation_keywords = ["NOTE", "SPEC", "DETAIL", "REF", "TYP"]
        for block in self.text_blocks:
            if any(kw in block["text"].upper() for kw in annotation_keywords):
                annotations.append(block["text"])

        components = ComplianceComponents(
            sheet_number=self.page_number,
            sheet_title=sheet_title,
            scale=scale,
            rooms=rooms,
            setbacks=setbacks,
            geometric_setbacks=geometric_setbacks,
            openings=openings,
            parking=parking,
            stairs=stairs,
            fire_safety=fire_safety,
            accessibility=accessibility,
            height_levels=height_levels,
            building_envelope=envelope,
            dimensions_found=dimensions,
            annotations=annotations[:50],  # Limit annotations
            # Site plan components
            lot_info=lot_info,
            adjacent_properties=adjacent_properties,
            water_features=water_features,
            north_pointer=north_pointer
        )

        # Build log message
        log_parts = [
            f"{len(rooms)} rooms", f"{len(setbacks)} setbacks",
            f"{len(geometric_setbacks)} geometric setbacks", f"{len(openings)} openings",
            f"{len(parking)} parking", f"{len(stairs)} stairs", f"{len(fire_safety)} fire safety",
            f"{len(accessibility)} accessibility", f"{len(height_levels)} height/levels",
            f"{len(dimensions)} dimensions"
        ]

        # Add site plan info to log
        if lot_info:
            log_parts.append(f"lot_info")
        if adjacent_properties:
            log_parts.append(f"{len(adjacent_properties)} adjacent properties")
        if water_features:
            log_parts.append(f"{len(water_features)} water features")
        if north_pointer and north_pointer.found:
            log_parts.append(f"north pointer")

        log(f"  Found: {', '.join(log_parts)}")

        return components


# =============================================================================
# Main Extraction Pipeline
# =============================================================================

def extract_compliance_components(pdf_path: Path) -> Dict[str, Any]:
    """Extract compliance components from all pages of a PDF."""
    all_components = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(tqdm(pdf.pages, desc="Processing pages")):
            extractor = ComponentExtractor(page, page_idx + 1)
            components = extractor.extract_all()
            all_components.append(components.to_dict())

    summary = {
        "total_sheets": len(all_components),
        "total_rooms": sum(len(c["rooms"]) for c in all_components),
        "total_setbacks": sum(len(c["setbacks"]) for c in all_components),
        "total_geometric_setbacks": sum(len(c["geometric_setbacks"]) for c in all_components),
        "total_openings": sum(len(c["openings"]) for c in all_components),
        "total_parking": sum(len(c["parking"]) for c in all_components),
        "total_stairs": sum(len(c["stairs"]) for c in all_components),
        "total_fire_safety": sum(len(c["fire_safety"]) for c in all_components),
        "total_accessibility": sum(len(c["accessibility"]) for c in all_components),
        "total_height_levels": sum(len(c["height_levels"]) for c in all_components),
        "room_types": list(set(
            room["room_type"]
            for c in all_components
            for room in c["rooms"]
        )),
    }

    return {
        "pdf_name": pdf_path.name,
        "summary": summary,
        "sheets": all_components
    }


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Extract compliance components from architectural PDF"
    )
    parser.add_argument("--pdf", required=True, help="Input PDF path")
    parser.add_argument("--output", help="Output JSON path (optional)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    log(f"Processing {pdf_path.name}...")
    result = extract_compliance_components(pdf_path)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.with_name(pdf_path.stem + "_components.json")

    # Save results
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    log(f"✅ Components extracted and saved to {output_path}")
    log(f"\nSummary:")
    log(f"  Sheets: {result['summary']['total_sheets']}")
    log(f"  Rooms: {result['summary']['total_rooms']}")
    log(f"  Setbacks (annotated): {result['summary']['total_setbacks']}")
    log(f"  Setbacks (geometric): {result['summary']['total_geometric_setbacks']}")
    log(f"  Openings: {result['summary']['total_openings']}")
    log(f"  Parking: {result['summary']['total_parking']}")
    log(f"  Stairs/Ramps: {result['summary']['total_stairs']}")
    log(f"  Fire Safety: {result['summary']['total_fire_safety']}")
    log(f"  Accessibility: {result['summary']['total_accessibility']}")
    log(f"  Height/Levels: {result['summary']['total_height_levels']}")
    log(f"  Room types found: {', '.join(result['summary']['room_types'])}")


if __name__ == "__main__":
    main()
