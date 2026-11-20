# Outgoing MTA Project Presentation Design

## Intent

Create a concise client-facing presentation that explains the outgoing MTA automation project as a story: the manual problem, the options considered, the chosen solution, how the system works, what the interface looks like, what has been verified, and what the next team should do.

## Audience

Innovation Partnerships staff, AI Clinic reviewers, U-M technical stakeholders, and the next project team. The deck must make sense without requiring the repository or technical documentation.

## Narrative

1. Introduce the project and client need.
2. Explain the existing manual process and its operational cost.
3. Show the source materials and constraints that shaped the work.
4. Compare the main solution choices and explain the hybrid approach.
5. Map the end-to-end system and backend responsibilities.
6. Explain deterministic eligibility rules and bounded NLP support.
7. Show template routing and population.
8. Walk through the real requester interface.
9. Show final document review and the one-sided SignNow flow.
10. Summarize milestones, representative test cases, and current results.
11. State project challenges and lessons without hiding unresolved scope.
12. Give the next team a prioritized product roadmap.

## Visual direction

- 16:9 PowerPoint deck using Michigan Blue, Maize, white, and light gray.
- Innovation Partnerships logo on the title slide and a restrained footer mark elsewhere.
- Flat editorial layouts rather than card-heavy dashboards.
- Editable native PowerPoint diagrams for process, decision, and signing flows.
- Use supplied screenshots of the live form and signing interface. Crop screenshots to the relevant interface area and label them plainly.
- Use a labeled placeholder for the private Streamlit demonstration URL because the exact link is not stored in the repository.

## Content constraints

- Use the current repository and verified project guide as the factual source.
- State that chemical, animal-derived, biological UBMTA, and device requests have active automated routes.
- Explain that production UBMTA routing still needs authoritative organization participation and signer verification.
- Explain BART as support for open-text evidence, not the final decision maker.
- Explain that the provider signature is already embedded and SignNow invites recipient-side signers only.
- Include the 190-test verification result and a clear manual-review example.
- Describe the future database and signed-document lifecycle as a recommendation, not as implemented functionality.
- Include challenges from the client work: incomplete scoping documents, inconsistent templates, undefined UBMTA operations, no assigned IT owner, and limited stakeholder access.

## Alternatives considered

- Technical architecture deck: strong for engineers but too narrow for client and clinic audiences.
- Executive summary deck: concise but would omit the workflow and interface evidence requested by the user.
- Narrative project review: combines the problem, design reasoning, working product, results, and handoff. This is the selected approach because it matches the supplied presentation plan.

## Deliverable

One editable PowerPoint deck in `docs/presentation/`, with all slides rendered and visually inspected before delivery.
