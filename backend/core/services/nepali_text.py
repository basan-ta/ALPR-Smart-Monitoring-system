from typing import Optional

# Simple digit map for Devanagari numerals
DEV_DIGITS = {
    '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
    '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'
}


def to_devanagari_digits_in_string(s: str) -> str:
    """Convert ASCII digits in a string to Devanagari digits, preserving other characters."""
    try:
        return ''.join(DEV_DIGITS.get(ch, ch) for ch in (s or ''))
    except Exception:
        return s or ''


# Curated Nepali first/middle names in Devanagari
MALE_FIRST_DEV = [
    'राम', 'हरि', 'सुमन', 'प्रकाश', 'पवन', 'दिपेश', 'रेमेश', 'नरेश', 'कृष्ण', 'विसाल',
    'लक्ष्मण', 'सुरज', 'अनिल', 'किरण', 'अजय', 'दीपक', 'सन्तोष', 'मनोज', 'नविन', 'राजन'
]
FEMALE_FIRST_DEV = [
    'सीता', 'गीता', 'राधा', 'सुनिता', 'बिमला', 'मिना', 'सरिता', 'अनीता', 'कञ्चन', 'बिना',
    'मनिषा', 'प्रमिला', 'सबिना', 'रुपा', 'अस्मिता', 'निर्मला', 'पवित्रा', 'रेखा', 'अनु', 'लक्ष्मी'
]

MALE_MIDDLE_DEV = ['बहादुर', 'प्रसाद', 'कुमार']
FEMALE_MIDDLE_DEV = ['देवी', 'कुमारी']

# Province-number (Devanagari) -> common surnames in Devanagari
SURNAMES_BY_PROVINCE_DEV = {
    '१': ['राई', 'लिम्बु', 'शेर्पा', 'कार्की', 'तामाङ'],          # Koshi
    '२': ['यादव', 'झा', 'मिश्रा', 'गुप्ता', 'चौधरी'],              # Madhesh
    '३': ['श्रेष्ठ', 'महर्जन', 'तामाङ', 'केसी', 'बस्नेत'],         # Bagmati
    '४': ['गुरुङ', 'मगर', 'थापा', 'पौडेल', 'अधिकारी'],           # Gandaki
    '५': ['थारु', 'चौधरी', 'अर्याल', 'न्यौपाने', 'शर्मा'],        # Lumbini
    '६': ['बीके', 'बुढा', 'शाही', 'भट्ट', 'रावत'],                # Karnali
    '७': ['चौधरी', 'बिष्ट', 'पाली', 'धामी', 'सिंह']               # Sudurpaschim
}


def pick_devanagari_name(province_dev: Optional[str], gender: str = 'male') -> str:
    """Pick a culturally aligned Nepali name (Devanagari), skewed by province when available."""
    import random
    g = (gender or 'male').strip().lower()
    if g not in ('male', 'female'):
        g = 'male'

    first = random.choice(MALE_FIRST_DEV if g == 'male' else FEMALE_FIRST_DEV)
    middle = random.choice(MALE_MIDDLE_DEV if g == 'male' else FEMALE_MIDDLE_DEV)

    surnames = SURNAMES_BY_PROVINCE_DEV.get(province_dev or '', [])
    if not surnames:
        # Fallback to a blended pool across provinces
        surnames = [
            'श्रेष्ठ', 'शर्मा', 'कार्की', 'बस्नेत', 'थापा', 'गुरुङ', 'मगर', 'राई', 'लिम्बु', 'तामाङ',
            'महर्जन', 'पौडेल', 'अधिकारी', 'न्यौपाने', 'चौधरी', 'बीके', 'भट्ट'
        ]
    last = random.choice(surnames)

    return f"{first} {middle} {last}"


def to_devanagari_text(s: Optional[str]) -> str:
    """Best-effort conversion of ASCII digits and common dash variants; leaves letters intact."""
    if s is None:
        return ''
    p = (s or '').strip()
    p = p.replace('—', '-').replace('–', '-')
    return to_devanagari_digits_in_string(p)