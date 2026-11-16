# Reference Files

This directory contains the approved eligibility checklist and the four clean DOCX agreement templates used by the proof of concept:

- `Template_AUTM_Animal.docx`
- `Template_Chemical_Materials.docx`
- `Template_Simple Letter_Device.docx`
- `Template_UBMTA_Biological.docx`

The SHA-256 hashes in `manifest.json` identify the exact files expected by the application and tests. The approved templates already contain Maggie Swift's provider-side signature, name, and title. The renderer adds the agreement-generation date beside that provider signature and populates the request-specific fields. SignNow tagging is applied only to the required recipient-side signature and date lines.
