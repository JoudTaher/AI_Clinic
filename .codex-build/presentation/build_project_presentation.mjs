import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "/Users/joudtaher/Documents/AI_Clinic";
const buildDir = path.join(workspaceDir, ".codex-build/presentation");
const renderDir = path.join(buildDir, "renders");
const outputPath = path.join(
  workspaceDir,
  "docs/presentation/Outgoing_MTA_Automation_Project_Presentation_Final.pptx",
);
const skillDir = "/Users/joudtaher/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations";
const runtimePython = "/Users/joudtaher/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";

const { finalizePresentation, makeNativeBulletParagraphs } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href
);

const W = 1280;
const H = 720;
const FONT = "Arial";
const BLUE = "#00274C";
const MID_BLUE = "#2F65A7";
const MAIZE = "#FFCB05";
const LIGHT_BLUE = "#E8F0F8";
const PALE = "#F5F7FA";
const GRAY = "#5B6573";
const LIGHT_GRAY = "#D9DEE5";
const WHITE = "#FFFFFF";
const BLACK = "#17202A";
const GREEN = "#2E7D5A";
const RED = "#A33B3B";

const logoPath = path.join(workspaceDir, "assets/innovation-partnerships.png");
const formShotPath = path.join(buildDir, "assets/interface-filled-top.png");
const signerShotPath = path.join(buildDir, "assets/interface-signing-plan.png");

async function arrayBufferFromFile(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addText(slide, text, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 24,
    bold: options.bold ?? false,
    color: options.color ?? BLACK,
    alignment: options.alignment ?? "left",
    verticalAlignment: options.verticalAlignment ?? "top",
    autoFit: options.autoFit ?? "shrinkText",
    insets: options.insets ?? 0,
    lineSpacing: options.lineSpacing ?? 1,
  };
  return shape;
}

function addRule(slide, left, top, width, color = MAIZE, height = 6) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
}

function addSlideTitle(slide, title, number, subtitle = "") {
  addText(slide, title, { left: 72, top: 44, width: 1030, height: 54 }, {
    fontSize: 38,
    bold: true,
    color: BLUE,
  });
  addRule(slide, 72, 108, 84, MAIZE, 7);
  if (subtitle) {
    addText(slide, subtitle, { left: 180, top: 104, width: 850, height: 34 }, {
      fontSize: 17,
      color: GRAY,
      verticalAlignment: "middle",
    });
  }
  addText(slide, String(number).padStart(2, "0"), { left: 1160, top: 52, width: 48, height: 28 }, {
    fontSize: 16,
    bold: true,
    color: MID_BLUE,
    alignment: "right",
  });
}

function addFooter(slide) {
  addText(slide, "U-M Innovation Partnerships | Outgoing MTA automation", {
    left: 72,
    top: 682,
    width: 620,
    height: 18,
  }, { fontSize: 11, color: GRAY });
}

function addBodyBullets(slide, items, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = makeNativeBulletParagraphs(items, {
    marginLeftPoints: options.marginLeftPoints ?? 20,
    hangingPoints: options.hangingPoints ?? 10,
    spaceAfterPoints: options.spaceAfterPoints ?? 10,
  });
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 24,
    color: options.color ?? BLACK,
    autoFit: "shrinkText",
    insets: 0,
  };
  return shape;
}

function addBox(slide, text, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: options.geometry ?? "roundRect",
    position,
    fill: options.fill ?? WHITE,
    line: {
      style: "solid",
      fill: options.line ?? LIGHT_GRAY,
      width: options.lineWidth ?? 1.5,
    },
    borderRadius: options.borderRadius ?? "rounded-lg",
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 21,
    bold: options.bold ?? true,
    color: options.color ?? BLUE,
    alignment: options.alignment ?? "center",
    verticalAlignment: "middle",
    autoFit: "shrinkText",
    insets: options.insets ?? 12,
  };
  return shape;
}

function connect(slide, from, to, options = {}) {
  return slide.shapes.connect(from, to, {
    kind: options.kind ?? "straight",
    fromSide: options.fromSide ?? "right",
    toSide: options.toSide ?? "left",
    line: { style: options.dashed ? "dashed" : "solid", fill: options.color ?? MID_BLUE, width: options.width ?? 2 },
    tail: { type: "arrow", width: "med", length: "med" },
  });
}

function addSectionLabel(slide, text, position, options = {}) {
  addText(slide, text.toUpperCase(), position, {
    fontSize: 14,
    bold: true,
    color: options.color ?? MID_BLUE,
    verticalAlignment: "middle",
  });
}

function addNote(slide, text) {
  slide.speakerNotes.text = text;
}

const presentation = Presentation.create({ slideSize: { width: W, height: H } });
const logo = await arrayBufferFromFile(logoPath);
const formShot = await arrayBufferFromFile(formShotPath);
const signerShot = await arrayBufferFromFile(signerShotPath);

// 1. Cover
{
  const slide = presentation.slides.add();
  slide.background.fill = BLUE;
  slide.shapes.add({
    geometry: "roundRect",
    position: { left: 58, top: 34, width: 610, height: 82 },
    fill: WHITE,
    line: { style: "solid", fill: WHITE, width: 0 },
    borderRadius: "rounded-lg",
  });
  slide.images.add({
    blob: logo,
    contentType: "image/png",
    fit: "contain",
    position: { left: 72, top: 46, width: 560, height: 58 },
  });
  addText(slide, "Outgoing MTA\nautomation", { left: 72, top: 190, width: 760, height: 190 }, {
    fontSize: 60,
    bold: true,
    color: WHITE,
    lineSpacing: 0.95,
  });
  addText(slide, "A proof of concept for eligibility, agreement preparation, review, and electronic signature", {
    left: 74,
    top: 410,
    width: 830,
    height: 88,
  }, { fontSize: 25, color: "#DDE8F3" });
  addRule(slide, 74, 538, 192, MAIZE, 9);
  addText(slide, "AI Clinic project review and handoff", { left: 74, top: 565, width: 560, height: 36 }, {
    fontSize: 19,
    bold: true,
    color: MAIZE,
  });
  addText(slide, "University of Michigan", { left: 980, top: 642, width: 230, height: 26 }, {
    fontSize: 15,
    color: WHITE,
    alignment: "right",
  });
  addNote(slide, "Introduce the project as a working proof of concept for Innovation Partnerships. The deck covers the problem, design reasoning, current workflow, and handoff recommendations.");
}

// 2. Manual problem
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "The manual outgoing MTA process", 2, "Repeated review and document handling created avoidable work");
  const labels = [
    "Requester form",
    "Checklist review",
    "Agreement choice",
    "Manual population",
    "Email and signing",
  ];
  const nodes = [];
  labels.forEach((label, i) => {
    nodes.push(addBox(slide, label, { left: 86 + i * 230, top: 220, width: 185, height: 88 }, {
      fill: i === 4 ? LIGHT_BLUE : PALE,
      line: i === 4 ? MID_BLUE : LIGHT_GRAY,
      fontSize: 20,
    }));
  });
  for (let i = 0; i < nodes.length - 1; i += 1) connect(slide, nodes[i], nodes[i + 1]);
  addText(slide, "The same facts moved between the questionnaire, checklist, Word templates, and email. Each transfer created another opportunity for inconsistent routing or copied values.", {
    left: 110,
    top: 380,
    width: 1060,
    height: 110,
  }, { fontSize: 28, color: BLUE, alignment: "center", verticalAlignment: "middle" });
  addRule(slide, 240, 535, 800, MAIZE, 5);
  addText(slide, "Client need", { left: 120, top: 570, width: 170, height: 34 }, { fontSize: 18, bold: true, color: MID_BLUE });
  addText(slide, "Automate routine standard requests while preserving legal rules, document review, and a manual route for exceptions.", {
    left: 300,
    top: 560,
    width: 830,
    height: 58,
  }, { fontSize: 22, color: BLACK });
  addFooter(slide);
  addNote(slide, "The department already had a process, but staff carried out the repeatable steps manually. The design target was the standard path, not every possible exception.");
}

// 3. Starting materials and constraints
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "Starting materials and constraints", 3, "The project began with policy, forms, templates, and incomplete operating context");
  addSectionLabel(slide, "Available", { left: 84, top: 170, width: 220, height: 26 });
  addBodyBullets(slide, [
    "Outgoing requester form",
    "Eligibility checklist for standard requests",
    "Chemical, animal, biological, and device agreements",
    "SignNow developer account",
  ], { left: 82, top: 210, width: 520, height: 300 }, { fontSize: 24, spaceAfterPoints: 14 });
  addSectionLabel(slide, "Constraints discovered", { left: 680, top: 170, width: 360, height: 26 }, { color: RED });
  addBodyBullets(slide, [
    "Agreement formats and field labels were inconsistent",
    "UBMTA had no defined standalone operating pipeline",
    "No assigned IT owner for authentication, hosting, or database work",
    "The team could not interview every production stakeholder",
  ], { left: 680, top: 210, width: 520, height: 315 }, { fontSize: 24, spaceAfterPoints: 14 });
  addText(slide, "These constraints shaped a focused proof of concept rather than a claim of production readiness.", {
    left: 210,
    top: 575,
    width: 860,
    height: 52,
  }, { fontSize: 24, bold: true, color: BLUE, alignment: "center" });
  addFooter(slide);
  addNote(slide, "The team treated the supplied documents as source material. Missing operational ownership and inconsistent templates became explicit handoff risks.");
}

// 4. Options and decision
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "Solution choices", 4, "A hybrid design matched the legal and technical risk");
  const cols = [90, 450, 810];
  const titles = ["Rules only", "AI first", "Hybrid approach"];
  const descriptions = [
    "Clear decisions, but weak handling of open-text evidence and wording variation.",
    "Flexible language handling, but unsafe for final legal eligibility decisions.",
    "Checklist rules decide eligibility. Local NLP supports only the open-text evidence that needs interpretation.",
  ];
  for (let i = 0; i < 3; i += 1) {
    addText(slide, titles[i], { left: cols[i], top: 190, width: 300, height: 46 }, {
      fontSize: 29,
      bold: true,
      color: i === 2 ? BLUE : GRAY,
      alignment: "center",
    });
    addRule(slide, cols[i] + 62, 248, 176, i === 2 ? MAIZE : LIGHT_GRAY, i === 2 ? 8 : 4);
    addText(slide, descriptions[i], { left: cols[i] + 10, top: 285, width: 280, height: 180 }, {
      fontSize: 23,
      color: i === 2 ? BLACK : GRAY,
      alignment: "center",
      verticalAlignment: "middle",
    });
  }
  addBox(slide, "Chosen", { left: 890, top: 490, width: 140, height: 46 }, {
    fill: MAIZE,
    line: MAIZE,
    color: BLUE,
    fontSize: 18,
  });
  addText(slide, "Reason: the checklist stays explainable and testable, while the language model reduces dependence on hard-coded phrases.", {
    left: 240,
    top: 565,
    width: 800,
    height: 62,
  }, { fontSize: 23, bold: true, color: BLUE, alignment: "center" });
  addFooter(slide);
  addNote(slide, "The system deliberately keeps policy in deterministic code. The language model supports specific evidence questions and never chooses the agreement or approves an exception.");
}

// 5. End-to-end workflow
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "End-to-end workflow", 5, "The backend separates intake, policy, documents, review, and delivery");
  const topLabels = ["Questionnaire", "Eligibility rules", "Template choice", "DOCX population"];
  const bottomLabels = ["Final review", "Confirmation", "SignNow", "Recipient signature"];
  const topNodes = [];
  const bottomNodes = [];
  topLabels.forEach((label, i) => topNodes.push(addBox(slide, label, {
    left: 90 + i * 285,
    top: 205,
    width: 225,
    height: 86,
  }, { fill: i === 1 ? LIGHT_BLUE : PALE, line: i === 1 ? MID_BLUE : LIGHT_GRAY, fontSize: 20 })));
  bottomLabels.forEach((label, i) => bottomNodes.push(addBox(slide, label, {
    left: 90 + (3 - i) * 285,
    top: 430,
    width: 225,
    height: 86,
  }, { fill: i === 0 ? "#FFF7D6" : PALE, line: i === 0 ? MAIZE : LIGHT_GRAY, fontSize: 20 })));
  for (let i = 0; i < topNodes.length - 1; i += 1) connect(slide, topNodes[i], topNodes[i + 1]);
  connect(slide, topNodes[3], bottomNodes[0], { kind: "elbow", fromSide: "bottom", toSide: "top" });
  for (let i = 0; i < bottomNodes.length - 1; i += 1) connect(slide, bottomNodes[i], bottomNodes[i + 1], { fromSide: "left", toSide: "right" });
  addText(slide, "Manual special-case review remains available whenever a rule fails, evidence stays unresolved, or no approved automated template applies.", {
    left: 180,
    top: 575,
    width: 920,
    height: 54,
  }, { fontSize: 22, color: BLUE, alignment: "center" });
  addFooter(slide);
  addNote(slide, "The review gate matters. The system never sends an agreement directly from the questionnaire without showing the values and generated document first.");
}

// 6. Rules and NLP
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "Eligibility rules and open-text evidence", 6, "The checklist controls the decision and BART handles bounded language questions");
  const intake = addBox(slide, "Submitted answers", { left: 80, top: 280, width: 210, height: 92 }, { fill: PALE, fontSize: 22 });
  const rules = addBox(slide, "Checklist rules", { left: 370, top: 190, width: 220, height: 92 }, { fill: LIGHT_BLUE, line: MID_BLUE, fontSize: 22 });
  const nlp = addBox(slide, "Local BART model\nfor open text", { left: 370, top: 385, width: 220, height: 110 }, { fill: "#FFF7D6", line: MAIZE, fontSize: 21 });
  const pass = addBox(slide, "All applicable\nconditions pass", { left: 720, top: 165, width: 220, height: 94 }, { fill: "#E7F4EC", line: GREEN, color: GREEN, fontSize: 20 });
  const manual = addBox(slide, "Failed or unresolved\nmanual review", { left: 720, top: 300, width: 220, height: 94 }, { fill: "#FBEAEA", line: RED, color: RED, fontSize: 20 });
  const audit = addBox(slide, "Evidence and scores\nrecorded", { left: 720, top: 445, width: 220, height: 94 }, { fill: PALE, line: GRAY, color: BLUE, fontSize: 20 });
  connect(slide, intake, rules, { kind: "elbow", fromSide: "right", toSide: "left" });
  connect(slide, intake, nlp, { kind: "elbow", fromSide: "right", toSide: "left", color: MAIZE });
  connect(slide, rules, pass, { kind: "elbow" });
  connect(slide, rules, manual, { kind: "elbow" });
  connect(slide, nlp, manual, { kind: "elbow", color: MAIZE });
  connect(slide, nlp, audit, { kind: "elbow", color: GRAY });
  addText(slide, "Example manual route", { left: 990, top: 215, width: 200, height: 30 }, { fontSize: 16, bold: true, color: RED });
  addText(slide, "“Research in the chemistry class” does not establish that a chemical will not be used in humans. The condition stays unresolved.", {
    left: 990,
    top: 255,
    width: 205,
    height: 210,
  }, { fontSize: 19, color: BLACK });
  addFooter(slide);
  addNote(slide, "Structured answers remain primary. The local facebook/bart-large-mnli model supports permitted open-text evidence and records entailment, contradiction, and neutral scores.");
}

// 7. Routing and population
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "Agreement routing and population", 7, "Material category selects an approved template only after eligibility passes");
  const source = addBox(slide, "Eligible standard request", { left: 70, top: 288, width: 230, height: 94 }, { fill: LIGHT_BLUE, line: MID_BLUE, fontSize: 21 });
  const mappings = [
    ["Chemical", "Chemical agreement", 150, GREEN],
    ["Animal-derived", "Animal agreement", 270, GREEN],
    ["Device", "Simple device agreement", 390, GREEN],
    ["Biological", "Manual review\nUBMTA future", 510, RED],
  ];
  mappings.forEach(([category, template, top, color]) => {
    const cat = addBox(slide, category, { left: 420, top, width: 190, height: 74 }, { fill: PALE, line: LIGHT_GRAY, fontSize: 20 });
    const dest = addBox(slide, template, { left: 760, top, width: 260, height: 74 }, {
      fill: color === GREEN ? "#E7F4EC" : "#FBEAEA",
      line: color,
      color,
      fontSize: 19,
    });
    connect(slide, source, cat, { kind: "elbow", fromSide: "right", toSide: "left", color: MID_BLUE });
    connect(slide, cat, dest, { color });
  });
  addText(slide, "Each active template has its own tested population strategy for names, titles, addresses, material details, dates, fees, and signature blocks.", {
    left: 1040,
    top: 215,
    width: 170,
    height: 280,
  }, { fontSize: 19, color: BLUE, alignment: "center", verticalAlignment: "middle" });
  addFooter(slide);
  addNote(slide, "The system does not guess the closest template. Biological requests remain manual because the separate UBMTA operating process and persistent signature record have not been defined.");
}

// 8. Interface walkthrough
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "Requester interface", 8, "The form follows the source questionnaire and shows only relevant agreement fields");
  slide.images.add({
    blob: formShot,
    contentType: "image/png",
    fit: "contain",
    position: { left: 430, top: 150, width: 790, height: 445 },
    geometry: "roundRect",
    borderRadius: "rounded-lg",
  });
  addBodyBullets(slide, [
    "Required fields show clear labels and validation",
    "Material selection controls the relevant questions",
    "Preview tools load representative mock cases",
    "The final agreement review remains a separate step",
  ], { left: 76, top: 190, width: 320, height: 300 }, { fontSize: 22, spaceAfterPoints: 12 });
  addText(slide, "Private demonstration link", { left: 76, top: 525, width: 300, height: 28 }, { fontSize: 16, bold: true, color: MID_BLUE });
  addBox(slide, "[INSERT PRIVATE STREAMLIT URL]", { left: 76, top: 560, width: 310, height: 54 }, {
    fill: PALE,
    line: LIGHT_GRAY,
    color: GRAY,
    fontSize: 16,
  });
  addFooter(slide);
  addNote(slide, "The private Streamlit deployment provides a controlled demonstration link. The exact URL and access list belong in the deployment handoff record.");
}

// 9. Review and SignNow
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "Document review and one-sided signing", 9, "The requester confirms the populated document before SignNow delivery");
  slide.images.add({
    blob: signerShot,
    contentType: "image/png",
    fit: "contain",
    position: { left: 560, top: 145, width: 650, height: 366 },
    geometry: "roundRect",
    borderRadius: "rounded-lg",
  });
  const review = addBox(slide, "Review values\nand DOCX", { left: 80, top: 190, width: 190, height: 82 }, { fill: "#FFF7D6", line: MAIZE, fontSize: 20 });
  const confirm = addBox(slide, "Confirm current\ndocument", { left: 310, top: 190, width: 190, height: 82 }, { fill: PALE, fontSize: 20 });
  const send = addBox(slide, "SignNow sends\nrecipient invitation", { left: 195, top: 340, width: 220, height: 92 }, { fill: LIGHT_BLUE, line: MID_BLUE, fontSize: 20 });
  connect(slide, review, confirm);
  connect(slide, confirm, send, { kind: "elbow", fromSide: "bottom", toSide: "top" });
  addText(slide, "Maggie Swift’s provider signature, name, and title already appear in the approved templates. The configured account sends the invitation and does not become another signer.", {
    left: 85,
    top: 490,
    width: 410,
    height: 130,
  }, { fontSize: 21, color: BLUE });
  addFooter(slide);
  addNote(slide, "The review service addresses the client concern about typos reaching a signed agreement. Any change invalidates the earlier confirmation.");
}

// 10. Verification and milestones
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "Milestones and verification", 10, "The proof of concept covers the standard path and its failure boundaries");
  addText(slide, "190", { left: 85, top: 170, width: 250, height: 120 }, {
    fontSize: 84,
    bold: true,
    color: BLUE,
    alignment: "center",
  });
  addText(slide, "automated tests passing", { left: 80, top: 290, width: 260, height: 40 }, {
    fontSize: 21,
    color: GRAY,
    alignment: "center",
  });
  addBodyBullets(slide, [
    "Chemical, animal-derived, and device mock cases select the expected agreement",
    "Manual-review cases do not receive an automatic template",
    "Final review blocks stale or unconfirmed documents",
    "Signer plans and SignNow payloads match recipient-side roles",
  ], { left: 405, top: 175, width: 750, height: 290 }, { fontSize: 23, spaceAfterPoints: 13 });
  const milestones = ["Questionnaire", "Rules", "Templates", "Review", "SignNow", "Private demo"];
  const mNodes = milestones.map((label, i) => addBox(slide, label, {
    left: 72 + i * 198,
    top: 525,
    width: 155,
    height: 64,
  }, { fill: i === 5 ? "#FFF7D6" : PALE, line: i === 5 ? MAIZE : LIGHT_GRAY, fontSize: 17 }));
  for (let i = 0; i < mNodes.length - 1; i += 1) connect(slide, mNodes[i], mNodes[i + 1], { width: 1.5 });
  addFooter(slide);
  addNote(slide, "The verified suite covers intake, rules, model decision handling through controlled doubles, template selection, rendering, review, signing plans, SignNow payloads, references, and interface behavior.");
}

// 11. Challenges
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  addSlideTitle(slide, "Challenges and lessons", 11, "The next team should treat the operating model as seriously as the code");
  const items = [
    ["Scope", "No complete scoping document defined deliverables, outcomes, or production ownership."],
    ["Templates", "Agreement files use different structures, field labels, optional terms, and signer layouts."],
    ["UBMTA", "The biological agreement requires a separate process that stakeholders did not fully define."],
    ["IT ownership", "No assigned team covered authentication, hosting, website integration, or database services."],
    ["Stakeholders", "The project team could not validate every rule and operational handoff with all responsible offices."],
  ];
  items.forEach(([label, text], i) => {
    const top = 165 + i * 94;
    addText(slide, label, { left: 90, top, width: 170, height: 36 }, { fontSize: 22, bold: true, color: MID_BLUE });
    addText(slide, text, { left: 280, top: top - 2, width: 900, height: 58 }, { fontSize: 22, color: BLACK });
    addRule(slide, 90, top + 64, 1090, LIGHT_GRAY, 2);
  });
  addText(slide, "Team implication", { left: 90, top: 635, width: 170, height: 28 }, { fontSize: 16, bold: true, color: BLUE });
  addText(slide, "Future staffing needs strong backend and architecture capability, document testing, AI evaluation, and ongoing legal and process ownership.", {
    left: 275,
    top: 625,
    width: 900,
    height: 46,
  }, { fontSize: 20, color: BLUE });
  addFooter(slide);
  addNote(slide, "These are handoff risks, not defects hidden by the proof of concept. Production work needs named owners and approved operating decisions.");
}

// 12. Roadmap
{
  const slide = presentation.slides.add();
  slide.background.fill = BLUE;
  addText(slide, "Recommended next phase", { left: 72, top: 48, width: 800, height: 58 }, {
    fontSize: 40,
    bold: true,
    color: WHITE,
  });
  addText(slide, "Build on the existing backend instead of restarting the workflow", { left: 72, top: 112, width: 900, height: 34 }, {
    fontSize: 20,
    color: "#DDE8F3",
  });
  addRule(slide, 72, 160, 110, MAIZE, 7);
  const roadmap = [
    ["1", "Confirm ownership", "Name policy, template, IT, security, records, and support owners."],
    ["2", "Standardize templates", "Control versions, population markers, formatting, and signature blocks."],
    ["3", "Add authentication and records", "Implement U-M login, roles, a database, and approved document storage."],
    ["4", "Connect signed documents", "Use verified SignNow events to retrieve, checksum, store, and reconcile final records."],
    ["5", "Define the UBMTA workflow", "Confirm eligibility, signers, sequence, storage, and manual exceptions before automation."],
  ];
  roadmap.forEach(([num, label, text], i) => {
    const top = 205 + i * 88;
    addBox(slide, num, { left: 80, top, width: 48, height: 48 }, { fill: MAIZE, line: MAIZE, color: BLUE, fontSize: 21 });
    addText(slide, label, { left: 155, top: top - 2, width: 320, height: 32 }, { fontSize: 23, bold: true, color: WHITE });
    addText(slide, text, { left: 485, top: top - 2, width: 690, height: 48 }, { fontSize: 20, color: "#DDE8F3" });
  });
  addText(slide, "Target product", { left: 80, top: 655, width: 140, height: 24 }, { fontSize: 15, bold: true, color: MAIZE });
  addText(slide, "A secure standalone MTA service with persistent, searchable signed records", {
    left: 230,
    top: 648,
    width: 890,
    height: 32,
  }, { fontSize: 21, bold: true, color: WHITE });
  addNote(slide, "The next phase should preserve the verified intake, rules, routing, population, review, and signing modules. Production work should add institutional identity, records, hosting, monitoring, and ownership.");
}

await fs.mkdir(renderDir, { recursive: true });
for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  const bytes = new Uint8Array(await png.arrayBuffer());
  await fs.writeFile(path.join(renderDir, `slide-${String(index + 1).padStart(2, "0")}.png`), bytes);
}
const montage = await presentation.export({ format: "webp", montage: true });
await fs.writeFile(path.join(buildDir, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const draftPath = path.join(buildDir, "draft-project-presentation.pptx");
await (await PresentationFile.exportPptx(presentation)).save(draftPath);

const requirements = {
  explicitTotalSlideCount: 12,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  workspaceDir,
  candidatePath: draftPath,
  finalPath: outputPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  fontPolicy: { basis: "design", families: [FONT] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(workspaceDir, ".codex-finalizer/Outgoing_MTA_Automation_Project_Presentation_Final.validation.json"),
};

const result = await finalizePresentation(requirements);
console.log(JSON.stringify({ outputPath, result }, null, 2));
