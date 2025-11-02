import re
import random
from typing import Optional, Set

# Devanagari digits map (0-9)
DEV_DIGITS = {
    '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
    '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'
}


def to_devanagari_number(n: int, width: Optional[int] = None) -> str:
    s = str(max(0, int(n)))
    if width is not None:
        s = s.zfill(width)
    return ''.join(DEV_DIGITS.get(ch, ch) for ch in s)


def to_devanagari_digits_in_string(s: str) -> str:
    """Convert ASCII digits in a string to Devanagari digits, preserving other characters."""
    try:
        return ''.join(DEV_DIGITS.get(ch, ch) for ch in (s or ''))
    except Exception:
        # Fallback in case of unexpected input types
        return s or ''


def convert_plate_to_nepali(plate: str) -> str:
    """Best-effort conversion of a plate string to Nepali digit format.

    - Normalizes uncommon dashes to '-'
    - Converts ASCII digits to Devanagari digits
    - Leaves letters and other characters intact
    """
    try:
        p = (plate or '').strip()
        # Normalize dash variants to standard hyphen-minus
        p = p.replace('—', '-').replace('–', '-')
        return to_devanagari_digits_in_string(p)
    except Exception:
        return plate or ''


# Provincial plate pattern (modern format), e.g.
# "प्रदेश ३-०१-१२ च १२३४"
REGEX_PROVINCIAL = re.compile(r"^प्रदेश\s[०-९]{1,2}[-–][०-९]{2}[-–][०-९]{2}\s[क-ह]\s[०-९]{4}$")

# Legacy zone-based pattern (older format), simplified common zones subset
# e.g. "बा १२ प १२३४"
REGEX_LEGACY = re.compile(r"^(बा|मे|को|सा|ज|भ|रा|लु|का|मा|ना)\s[०-९]{2}\s[क-ह]\s[०-९]{4}$")


CLASS_LETTERS = [
    'क', 'ख', 'ग', 'घ', 'च', 'छ', 'ज', 'ट', 'ठ', 'ड', 'ढ', 'त', 'थ', 'द', 'ध', 'न',
    'प', 'फ', 'ब', 'भ', 'म', 'य', 'र', 'ल', 'व', 'श', 'ष', 'स', 'ह'
]

LEGACY_ZONES = ['बा', 'मे', 'को', 'सा', 'ज', 'भ', 'रा', 'लु', 'का', 'मा', 'ना']


def normalize_plate(plate: str) -> str:
    p = (plate or '').strip()
    return p.replace('—', '-').replace('–', '-')


def is_valid_nepali_plate(plate: str) -> bool:
    p = normalize_plate(plate)
    return bool(REGEX_PROVINCIAL.match(p) or REGEX_LEGACY.match(p))


def generate_provincial_plate() -> str:
    prov = random.randint(1, 7)
    area = random.randint(1, 99)
    series = random.randint(1, 99)
    letter = random.choice(CLASS_LETTERS)
    num = random.randint(1000, 9999)
    return f"प्रदेश {to_devanagari_number(prov)}-{to_devanagari_number(area, 2)}-{to_devanagari_number(series, 2)} {letter} {to_devanagari_number(num, 4)}"


def generate_legacy_plate() -> str:
    zone = random.choice(LEGACY_ZONES)
    series = random.randint(1, 99)
    letter = random.choice(CLASS_LETTERS)
    num = random.randint(1000, 9999)
    return f"{zone} {to_devanagari_number(series, 2)} {letter} {to_devanagari_number(num, 4)}"


def generate_unique(prefer: str = 'provincial', existing: Optional[Set[str]] = None) -> str:
    tries = 0
    while True:
        plate = generate_provincial_plate() if prefer == 'provincial' else generate_legacy_plate()
        if is_valid_nepali_plate(plate) and (existing is None or plate not in existing):
            return plate
        tries += 1
        if tries > 1000:
            raise RuntimeError('Failed to generate unique Nepali plate')


def extract_province_from_plate(plate: str) -> Optional[str]:
    """Return Devanagari province number (e.g., '३') if present, else None."""
    p = normalize_plate(plate)
    m = REGEX_PROVINCIAL.match(p)
    if not m:
        return None
    # Split "प्रदेश X-YY-ZZ L NNNN"
    try:
        body = p.split()[1]  # X-YY-ZZ
        return body.split('-')[0]  # X in Devanagari
    except Exception:
        return None