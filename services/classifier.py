"""
Classifier Service
===================
Pure business logic for complaint classification — zero Flask dependencies.

Responsibilities:
  1. Category definitions (crime & civic) with keywords, legal sections, labels
  2. Crime-vs-civic scoring
  3. Sub-category detection (best keyword-match within a category group)
  4. Location extraction from free-text complaints

Extracted from routes/complaints.py in Step 3.
"""
import re
from ml.ml_model import classifier_instance

# ── Pre-compiled location extraction regex ────────────────────────────────
LOC_PATTERN = re.compile(
    r'((?:[a-zA-Z0-9-,]+\s+){1,6}'
    r'(?:street|road|cross|layout|nagar|colony|block|market|area|park'
    r'|junction|circle|highway|avenue|sector|phase|st|rd)'
    r'(?:\s+[a-zA-Z0-9-,]+){0,2})',
    re.IGNORECASE
)

# ── Crime Category Definitions ────────────────────────────────────────────
CRIME_CATEGORIES = {
    'theft': {
        'keywords': ['snatch', 'rob', 'steal', 'theft', 'chain', 'purse',
                     'pickpocket', 'burglary', 'loot'],
        'sections': 'BNS Sec. 303 (Theft), BNS Sec. 304 (Snatching/Robbery)',
        'category': 'Theft / Robbery',
    },
    'assault': {
        'keywords': ['assault', 'attack', 'beat', 'stab', 'hit', 'punch', 'slap', 'injured'],
        'sections': 'BNS Sec. 115 (Voluntarily Causing Hurt), BNS Sec. 117 (Grievous Hurt)',
        'category': 'Physical Assault',
    },
    'sexual_offense': {
        'keywords': ['molest', 'rape', 'harass', 'stalk', 'eve-tease', 'grope', 'sexual'],
        'sections': 'BNS Sec. 63 (Rape), BNS Sec. 74 (Assault on Woman), BNS Sec. 78 (Stalking)',
        'category': 'Sexual Offense',
    },
    'murder': {
        'keywords': ['murder', 'kill', 'shoot', 'dead', 'death', 'homicide'],
        'sections': 'BNS Sec. 101 (Murder), BNS Sec. 103 (Culpable Homicide)',
        'category': 'Murder / Homicide',
    },
    'kidnapping': {
        'keywords': ['kidnap', 'abduct', 'missing', 'taken', 'hostage'],
        'sections': 'BNS Sec. 137 (Kidnapping), BNS Sec. 140 (Abduction)',
        'category': 'Kidnapping / Abduction',
    },
    'extortion': {
        'keywords': ['extortion', 'threat', 'blackmail', 'ransom', 'intimidat'],
        'sections': 'BNS Sec. 308 (Extortion), BNS Sec. 351 (Criminal Intimidation)',
        'category': 'Extortion / Threats',
    },
    'general_crime': {
        'keywords': ['crime', 'scared', 'abuse', 'fraud', 'cheat'],
        'sections': 'BNS Sec. 318 (Cheating), BNS Sec. 109 (Attempt to Commit Offence)',
        'category': 'Criminal Offense',
    },
}

# ── Civic Category Definitions ────────────────────────────────────────────
CIVIC_CATEGORIES = {
    'water': {
        'keywords': ['water', 'pipe', 'leak', 'supply', 'tank', 'bore'],
        'sections': 'Municipal Corporation Act, Sec. 298 (Water Supply Maintenance)',
        'category': 'Water Supply Issue',
    },
    'roads': {
        'keywords': ['pothole', 'road', 'highway', 'footpath', 'bridge', 'pavement'],
        'sections': 'Municipal Corporation Act, Sec. 231 (Road & Infrastructure Maintenance)',
        'category': 'Road / Infrastructure Damage',
    },
    'sanitation': {
        'keywords': ['garbage', 'waste', 'clean', 'sewer', 'drain', 'flood'],
        'sections': 'Municipal Solid Waste Rules, 2016; Municipal Corporation Act, Sec. 302',
        'category': 'Sanitation / Drainage',
    },
    'electricity': {
        'keywords': ['electric', 'light', 'power', 'pole', 'transformer', 'wire'],
        'sections': 'Electricity Act, 2003; Municipal Corporation Act, Sec. 305',
        'category': 'Electricity / Street Lighting',
    },
    'environment': {
        'keywords': ['noise', 'pollution', 'construction', 'park', 'tree', 'air'],
        'sections': 'Environment Protection Act, 1986; Noise Pollution Rules, 2000',
        'category': 'Environmental Issue',
    },
    'general_civic': {
        'keywords': [],
        'sections': 'Municipal Corporation Act (General Grievance)',
        'category': 'General Civic Issue',
    },
}

# Flat keyword lists for top-level crime vs. civic scoring
CRIME_KEYWORDS = [kw for cat in CRIME_CATEGORIES.values() for kw in cat['keywords']]
CIVIC_KEYWORDS = [kw for cat in CIVIC_CATEGORIES.values() for kw in cat['keywords']]


# ── Classification Functions ──────────────────────────────────────────────

def detect_sub_category(text_lower: str, categories: dict) -> str | None:
    """Return the category key with the most keyword hits, or None."""
    best_cat = None
    best_score = 0
    for cat_name, cat_data in categories.items():
        score = sum(1 for kw in cat_data['keywords'] if kw in text_lower)
        if score > best_score:
            best_score = score
            best_cat = cat_name
    return best_cat


def classify_complaint(text_lower: str) -> dict:
    """
    Classify a complaint as crime or civic and return full metadata.

    Returns a dict with keys:
        incident_type, category, sections, department, priority,
        sla, submitted_to, target_email_key, confidence
    """
    if classifier_instance.is_loaded:
        pred = classifier_instance.predict(text_lower)
        sub_cat = pred['label']
        confidence = pred['confidence']

        if sub_cat in CRIME_CATEGORIES:
            cat_data = CRIME_CATEGORIES.get(sub_cat, CRIME_CATEGORIES['general_crime'])
            return {
                'incident_type': 'crpc_crime',
                'category': cat_data['category'],
                'sections': cat_data['sections'],
                'department': 'Local Police Station',
                'priority': 'High',
                'sla': 'Immediate FIR Registration',
                'submitted_to': 'Station House Officer (SHO), Local Police Jurisdiction',
                'target_email_key': 'POLICE_EMAIL',
                'confidence': confidence
            }
        else:
            cat_data = CIVIC_CATEGORIES.get(sub_cat, CIVIC_CATEGORIES['general_civic'])
            return {
                'incident_type': 'civic_issue',
                'category': cat_data['category'],
                'sections': cat_data['sections'],
                'department': 'Municipal Corporation',
                'priority': 'Medium',
                'sla': '24-48 Hours',
                'submitted_to': 'Chief Zonal Officer, Public Works & Sanitation Dept',
                'target_email_key': 'CIVIC_EMAIL',
                'confidence': confidence
            }

    # Fallback to keyword-based logic if ML model is not loaded
    crime_score = sum(1 for kw in CRIME_KEYWORDS if kw in text_lower)
    civic_score = sum(1 for kw in CIVIC_KEYWORDS if kw in text_lower)

    if crime_score > civic_score:
        sub_cat = detect_sub_category(text_lower, CRIME_CATEGORIES)
        cat_data = CRIME_CATEGORIES.get(sub_cat, CRIME_CATEGORIES['general_crime'])
        return {
            'incident_type': 'crpc_crime',
            'category': cat_data['category'],
            'sections': cat_data['sections'],
            'department': 'Local Police Station',
            'priority': 'High',
            'sla': 'Immediate FIR Registration',
            'submitted_to': 'Station House Officer (SHO), Local Police Jurisdiction',
            'target_email_key': 'POLICE_EMAIL',
            'confidence': 0.0
        }
    else:
        sub_cat = detect_sub_category(text_lower, CIVIC_CATEGORIES)
        cat_data = CIVIC_CATEGORIES.get(sub_cat, CIVIC_CATEGORIES['general_civic'])
        return {
            'incident_type': 'civic_issue',
            'category': cat_data['category'],
            'sections': cat_data['sections'],
            'department': 'Municipal Corporation',
            'priority': 'Medium',
            'sla': '24-48 Hours',
            'submitted_to': 'Chief Zonal Officer, Public Works & Sanitation Dept',
            'target_email_key': 'CIVIC_EMAIL',
            'confidence': 0.0
        }


def extract_location(text: str) -> str | None:
    """
    Extract a street-level location from free-text complaint narrative.

    Returns the cleaned, title-cased location string, or None if no match.
    """
    match = LOC_PATTERN.search(text)
    if not match:
        return None
    extracted = match.group(1).strip().title()
    # Strip leading prepositions
    extracted = re.sub(
        r'^(At|On|In|Near|Opposite|Outside|Behind|Around)\s+',
        '', extracted, flags=re.IGNORECASE
    )
    return extracted


def build_summary(incident_type: str, category: str, safe_text_prefix: str) -> str:
    """Generate an AI-style summary sentence for the complaint."""
    if incident_type == 'crpc_crime':
        return (
            f"The complainant reported a critical incident involving {category.lower()}. "
            f"The text indicates: {safe_text_prefix}... Required immediate intelligence routing."
        )
    return (
        f"The citizen reported a civic issue related to {category.lower()}. "
        f"Issue overview: {safe_text_prefix}... Requires standard municipal intervention workflow."
    )
