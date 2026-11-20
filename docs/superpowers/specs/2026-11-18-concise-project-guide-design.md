# Concise Project Guide Design

## Intent

Replace the current long technical report with a practical handoff guide for Innovation Partnerships staff, U-M IT, and the next development team. The guide explains the problem, the source material available to the project, the implemented solution and its rationale, the current boundary, and the recommended next work.

## Content and order

1. Project purpose and problem
2. Source materials and constraints
3. Current solution and end-to-end workflow
4. Why the main technologies and controls were chosen
5. Current verification, including representative cases and one manual-review example
6. Deployment and operational boundary
7. Challenges and warnings for the next team
8. Research completed
9. Future product development and recommendations

## Writing and presentation rules

- Maximum 10 rendered pages; target 7 to 9 pages.
- Black text only, no tables, colored fills, diagrams, callout boxes, or decorative elements.
- Use short sections, ordinary paragraphs, numbered steps, and limited bullet lists.
- Keep code-level details to names needed to understand ownership and behavior; include no code snippets.
- Separate current capabilities from future work explicitly.
- Do not compare standalone and integrated products. Recommend one standalone product with a database and approved signed-document storage.
- Describe UBMTA as the active biological-material route in the proof of concept, with organization and signer verification as production work.
- Explain the relative termination clause and why the current system does not calculate a calendar termination date before signing.

## Accuracy boundaries

- Chemical, animal-derived, biological UBMTA, and device mock workflows are automated.
- SignNow Development Mode sends recipient-side invitations only after final document review and confirmation. Provider-side signature information is already embedded in the approved templates.
- The current proof of concept has no production database, webhook receiver, completed-document retrieval, institutional authentication, or authoritative archive.
- The private hosted link is an access mechanism, not evidence of production readiness.
