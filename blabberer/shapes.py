"""
Preston Blair 9-shape mouth definitions for lip sync sprite generation.

Each shape maps to specific phonemes and includes:
- reference_file: cartoon reference image (bundled in reference/ directory)
- phonemes: the sounds this shape represents
- anatomical_desc: precise description for photorealistic generation
"""

SHAPE_DEFS = {
    "shape_A": {
        "reference_file": "BMP.webp",
        "phonemes": "M, B, P",
        "anatomical_desc": (
            "Lips gently pressed together with slight natural compression. "
            "Both lips are sealed — no gap, no teeth visible. "
            "The jaw is relaxed and closed. Think of the moment you say 'mmm'. "
            "The lips should look natural and relaxed, not pursed or tense."
        ),
    },
    "shape_B": {
        "reference_file": "CDGKNSTXYZ.webp",
        "phonemes": "C, D, G, K, N, S, T, Y, Z",
        "anatomical_desc": (
            "Lips slightly parted with upper and lower teeth close together and visible. "
            "The jaw is barely open — teeth are almost touching. "
            "The lips are relaxed and neutral, pulled back just enough to show the teeth. "
            "This is a natural talking position, NOT a smile. "
            "Think of how the mouth looks when saying 'set' or 'ten'."
        ),
    },
    "shape_C": {
        "reference_file": "AEI.webp",
        "phonemes": "A, I",
        "anatomical_desc": (
            "Mouth open to a moderate, natural speaking position. "
            "The jaw drops about 1.5 centimeters — a relaxed, calm opening. "
            "Upper teeth visible, lower teeth may be partially visible. "
            "The lips are relaxed and open, not stretched or pulled. "
            "Think of calmly saying 'father' or 'high' in conversation. "
            "IMPORTANT: This is NOT yawning, NOT screaming, NOT surprised. "
            "Just a calm, natural open mouth during normal speech."
        ),
    },
    "shape_D": {
        "reference_file": "E.webp",
        "phonemes": "E",
        "anatomical_desc": (
            "Lips stretched slightly horizontally with moderate jaw opening. "
            "The mouth corners pull gently to the sides. "
            "Upper and lower teeth visible through the opening. "
            "The jaw drops a bit more than the consonant position. "
            "Think of naturally saying 'bed' or 'get'. "
            "This is a subtle horizontal stretch — NOT a grin, NOT a big smile."
        ),
    },
    "shape_E": {
        "reference_file": "O.webp",
        "phonemes": "O",
        "anatomical_desc": (
            "Lips form a moderate rounded oval shape. "
            "The jaw drops slightly and the lips round into a gentle O. "
            "The opening is distinctly round — not wide, not flat. "
            "Think of naturally saying 'go' or 'oh' in conversation. "
            "The rounding should be subtle and natural — not exaggerated like a cartoon O."
        ),
    },
    "shape_F": {
        "reference_file": "QW.webp",
        "phonemes": "U, W, Q",
        "anatomical_desc": (
            "Lips pushed slightly forward into a small, tight rounded opening. "
            "The lips protrude gently, forming a small circular hole. "
            "Much smaller opening than the O shape. "
            "Think of the start of saying 'who' or 'wood'. "
            "The pucker should be subtle and natural — NOT an exaggerated duck face or kiss."
        ),
    },
    "shape_G": {
        "reference_file": "FV.webp",
        "phonemes": "F, V",
        "anatomical_desc": (
            "Upper front teeth gently resting on the lower lip. "
            "The upper lip lifts slightly to expose the upper teeth. "
            "The lower lip tucks naturally under the upper front teeth. "
            "Think of naturally saying 'five' or 'very'. "
            "The contact between teeth and lower lip should be gentle and natural."
        ),
    },
    "shape_H": {
        "reference_file": "L.webp",
        "phonemes": "T, L, D, N",
        "anatomical_desc": (
            "Lips BARELY parted — just a very small, subtle gap between the lips. "
            "The mouth is only slightly open, about 3-4 millimeters of opening. "
            "The tongue is inside touching the palate but is NOT visible from outside. "
            "This is an extremely subtle shape — the lips separate just enough to show "
            "a thin sliver of darkness between them. No teeth visible. "
            "Think of how the mouth looks at the very start of saying 'let' or 'no' — "
            "the lips part only slightly. This should look almost like the rest pose "
            "but with the lips just barely separated."
        ),
    },
}

PROMPT_TEMPLATE = """I am showing you two images:
- IMAGE 1 (first): A photograph of a real person's face (the character).
- IMAGE 2 (second): A cartoon reference showing the target mouth position for the sound "{phonemes}".

Edit ONLY the mouth area of IMAGE 1 (the photograph) to match the general mouth position shown in IMAGE 2 (the cartoon reference), but adapted for a REAL HUMAN face.

Target mouth position: {anatomical_desc}

CRITICAL RULES:
- The result MUST be photorealistic — this is a real person, not a cartoon
- The mouth change should be SUBTLE and NATURAL, much less exaggerated than the cartoon reference
- Maintain the person's exact skin texture, skin color, lighting, wrinkles, and complexion
- Do NOT alter the color saturation, brightness, or contrast of the image
- Do NOT make the expression look emotional, seductive, surprised, or dramatic
- The person should look like they are calmly speaking, nothing more
- Do NOT change hair, clothing, or background

NATURAL FACIAL RESPONSE:
- When the mouth moves, the surrounding face should respond naturally — just like a real person speaking
- Cheeks may lift or compress slightly depending on the mouth shape
- Nasolabial folds (lines from nose to mouth corners) should deepen or soften naturally with the mouth position
- Eyebrows and eyes may shift very subtly — a slight narrowing or lift that naturally accompanies calm speech
- These secondary movements should be VERY SUBTLE — this is calm conversation, not acting
- The overall expression must remain neutral and conversational

FACIAL HAIR PRESERVATION (very important):
- If the person has a beard, keep the EXACT same beard — same shape, density, color, and coverage
- If the person has a moustache, keep the EXACT same moustache — do NOT add, remove, or reshape it
- If the person does NOT have a moustache, do NOT add one
- If the person does NOT have a beard, do NOT add one
- Facial hair must remain identical to IMAGE 1 except where the lips themselves move
- Do NOT change sideburns, chin hair, or any hair on the face"""


def get_shape_names():
    """Return list of shape names (A-H), excluding X which is the idle pose."""
    return [f"shape_{c}" for c in "ABCDEFGH"]


def get_all_shape_names():
    """Return list of all shape names (A-H + X)."""
    return [f"shape_{c}" for c in "ABCDEFGHX"]
