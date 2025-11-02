Nepali ANPR Processed Dataset

- Files:
  - `nepali_processed_dataset.json` — transformed records preserving original schema keys
  - `nepali_processed_metadata.json` — metadata, validation rules, QA summary, references

Overview
- This dataset is derived from the running Django ORM (core models) and transformed to use authentic Nepali-style license plates and culturally aligned owner names.
- The content preserves the original data structure:
  - `vehicles`: `[ { id, plate_number, status, owner, last_seen, notes, created_at, updated_at } ]`
  - Optional `sightings`: `[ { id, plate_number, vehicle, vehicle_type, color, latitude, longitude, speed_kmh, heading_deg, timestamp } ]`
  - Optional `alerts`: `[ { id, plate_number, vehicle, status, timestamp, predicted_latitude, predicted_longitude, message, acknowledged, dispatched, created_at } ]`

License Plate Formats
- Modern provincial pattern (validated): `^प्रदेश [०-९]{1,2}-[०-९]{2}-[०-९]{2} [क-ह] [०-९]{4}$`
- Legacy zone pattern (validated): `^(बा|मे|को|सा|ज|भ|रा|लु|का|मा|ना) [०-९]{2} [क-ह] [०-९]{4}$`
- Examples:
  - `प्रदेश ३-०१-१२ च १२३४`
  - `बा १२ प १२३४`

Name Transformation
- Owner names are replaced with common Nepali names aligned to regional surnames:
  - Male: first name + one of {Bahadur, Prasad, Kumar} + regional surname
  - Female: first name + one of {Devi, Kumari} + regional surname
- Regional surname distributions:
  - Province १ (Koshi): Rai, Limbu, Sherpa, Karki, Tamang
  - Province २ (Madhesh): Yadav, Jha, Mishra, Gupta, Chaudhary
  - Province ३ (Bagmati): Shrestha, Maharjan, Tamang, KC, Basnet
  - Province ४ (Gandaki): Gurung, Magar, Thapa, Poudel, Adhikari
  - Province ५ (Lumbini): Tharu, Chaudhary, Aryal, Neupane, Sharma
  - Province ६ (Karnali): BK, Budha, Shahi, Bhatta, Rawat
  - Province ७ (Sudurpashchim): Bhatta, Joshi, Chaudhary, Tiwari, Khadka

Quality Assurance
- All generated plates validated against the patterns above.
- Name-gender alignment enforced via culturally typical middle names.
- Notes fields cleared to ensure no PII remains.
- See `nepali_processed_metadata.json` for counts, validation flags, and transformation timestamps.

References
- Automatic Nepali Number Plate Recognition with Support Vector Machines — https://www.researchgate.net/publication/323999303_Automatic_Nepali_Number_Plate_Recognition_with_Support_Vector_Machines
- LPR dataset for Nepali motorbike license plate — https://github.com/Prasanna1991/LPR