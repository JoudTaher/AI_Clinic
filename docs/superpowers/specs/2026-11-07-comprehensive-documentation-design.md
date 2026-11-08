# Comprehensive MTA Automation Documentation Design

## Intent

Create one authoritative document that explains the University of Michigan Outgoing MTA Automation proof of concept from product, operational, research, and technical perspectives. The document should help Innovation Partnerships stakeholders understand the value and limitations of the work, help U-M IT evaluate what would be required for institutional deployment, and give a future developer enough context to maintain and extend the system.

## Audience

- Innovation Partnerships staff and project sponsors
- U-M IT, security, identity, and integration teams
- Future developers and technical maintainers
- AI Clinic reviewers and portfolio readers who need an accurate account of the work

## Chosen approach

Use one master Microsoft Word document under `docs/` and link it from the repository README. A single source avoids repetition and prevents the product, architecture, and roadmap descriptions from drifting apart. The document will use a layered structure: concise context first, followed by operational and technical detail, then appendices for exact mappings and terminology.

## Content structure

1. Executive overview and problem statement
2. Project goals, scope, and stakeholders
3. Source documents and research basis
4. Current user journey and end-to-end workflow
5. Eligibility checklist and decision logic
6. Open-text semantic analysis and present AI usage
7. Material classification and agreement-template mapping
8. Agreement data collection and DOCX population
9. Signing roles, local packages, and SignNow Development Mode
10. System architecture and module responsibilities
11. Request, decision, artifact, and audit data flows
12. Configuration, installation, operation, and testing
13. Security, privacy, accessibility, reliability, and governance considerations
14. Current limitations and proof-of-concept boundaries
15. Future-state architecture and prioritized roadmap
16. Responsible AI opportunities and adoption stages
17. Deployment, authentication, database, integration, and operational requirements
18. Success measures, risks, and recommended next steps
19. Appendices containing exact rules, mappings, statuses, and glossary

## Accuracy rules

- Clearly label each capability as implemented, Development Mode, researched/designed, or proposed.
- Treat the supplied eligibility checklist as the authority for automatic-approval criteria.
- Treat the supplied requester form as the source for questionnaire fields.
- Treat the supplied agreement files as the authority for population and signature fields.
- Do not imply that the proof of concept currently provides U-M authentication, eRPM integration, production database storage, production SignNow activation, webhook tracking, or institutional hosting.
- Do not describe probabilistic NLP output as a legal or compliance decision by itself.
- Do not overstate AI. The system is primarily deterministic workflow automation; local semantic classification is a narrow supporting capability.
- Preserve the established terminology: a request meeting every applicable checklist criterion qualifies for Standard MTA automatic approval; all other cases require manual special-case review.

## Writing style

- Natural, direct, and professional rather than promotional or AI-generated in tone
- Specific enough for technical handoff without assuming every reader is a developer
- Minimal repetition, short transitions, and concrete examples where they clarify behavior
- Recommendations should be practical for the department's present resources
- Future AI capabilities should be framed as staged options with prerequisites, risks, and human-governance requirements

## Deliverables

- `docs/University_of_Michigan_Outgoing_MTA_Automation_Documentation.docx`
- A short link and description added to `README.md`
- Verification against the current code, tests, configuration, templates, and existing requirements/design records
- Page-by-page rendered visual review of the final Word document

## Non-goals

- Changing application behavior or legal agreement language
- Adding new product features during documentation work
- Presenting speculative integrations as committed U-M architecture
- Replacing official legal, security, privacy, accessibility, or records-management review
