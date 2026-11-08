# Agreement Template Naming Design

## Intent

Remove the misleading agreement names from the automation pipeline so each request category maps to one plainly named agreement template, while preserving the supplied legal document contents and the existing eligibility rules.

## Canonical mapping

| Request category | Template ID | Reference file |
| --- | --- | --- |
| Chemical material | `chemical_material_agreement` | `Template_Chemical_Materials.docx` |
| Biological material | `biological_material_agreement` | `Template_UBMTA_Biological.docx` |
| Animal material | `animal_material_agreement` | `Template_AUTM_Animal.docx` |
| Device material | `device_material_agreement` | `Template_Simple Letter_Device.docx` |

## Constraints

- The malformed `Template_AUTM_Animaldocx` filename is corrected to `Template_AUTM_Animal.docx`.
- Material categories and checklist sections remain unchanged; only agreement template identities and references are renamed.
- The form continues to collect one canonical set of organization, scientist, material, shipping, and signing fields and reuses them in the selected agreement.
- The legal text and layout of the four supplied DOCX files are not rewritten.
- SignNow role placement and signing order remain unchanged.
- No previous template ID or filename may remain in executable code, tests, the catalog, the reference manifest, or reference documentation.

## Approach

Use material-oriented template IDs throughout the application and keep format-specific rendering methods private to the DOCX adapter. This makes the business pipeline readable without pretending the legal agreements have identical structures.

