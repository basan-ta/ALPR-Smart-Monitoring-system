// Nepali plate utilities for frontend validation and formatting

// Devanagari digits map (0-9)
export const DEV_DIGITS = {
  '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
  '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'
};

export function toDevanagariNumber(n, width) {
  const s = String(Math.max(0, parseInt(n || 0, 10)));
  const padded = (typeof width === 'number') ? s.padStart(width, '0') : s;
  return padded.split('').map(ch => DEV_DIGITS[ch] || ch).join('');
}

export function normalizePlate(plate) {
  const p = String(plate || '').trim();
  return p.replace(/—|–/g, '-');
}

// Regex patterns mirror backend/core/services/nepali_plates.py
// Provincial (modern): "प्रदेश X-YY-ZZ L NNNN"
const REGEX_PROVINCIAL = new RegExp(
  String.raw`^प्रदेश\s[०-९]{1,2}[-–][०-९]{2}[-–][०-९]{2}\s[क-ह]\s[०-९]{4}$`
);

// Legacy zone-based: e.g., "बा १२ प १२३४"
const REGEX_LEGACY = new RegExp(
  String.raw`^(बा|मे|को|सा|ज|भ|रा|लु|का|मा|ना)\s[०-९]{2}\s[क-ह]\s[०-९]{4}$`
);

export function isValidNepaliPlate(plate) {
  const p = normalizePlate(plate);
  return REGEX_PROVINCIAL.test(p) || REGEX_LEGACY.test(p);
}

export function extractProvinceFromPlate(plate) {
  const p = normalizePlate(plate);
  if (!REGEX_PROVINCIAL.test(p)) return null;
  try {
    const body = p.split(/\s+/)[1]; // X-YY-ZZ
    return body.split('-')[0]; // X in Devanagari
  } catch {
    return null;
  }
}

export const CLASS_LETTERS = [
  'क','ख','ग','घ','च','छ','ज','ट','ठ','ड','ढ','त','थ','द','ध','न',
  'प','फ','ब','भ','म','य','र','ल','व','श','ष','स','ह'
];