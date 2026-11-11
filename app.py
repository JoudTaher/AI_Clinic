from __future__ import annotations

import base64
import json
from html import escape
from collections.abc import Mapping
from pathlib import Path

import streamlit as st

from src.intake import evaluate_intake_readiness
from src.agreement_readiness import evaluate_agreement_readiness
from src.adapters.docx_renderer import DocxAgreementRenderer
from src.materials import (
    HUMAN_MATERIAL_TYPE,
    MATERIAL_TYPES,
    derive_material_categories,
)
from src.pipeline.outgoing_mta import OutgoingMTAPipeline
from src.screening_report import build_screening_report, serialize_screening_report
from src.signing import build_agreement_sender
from src.signing.plan import build_signer_plan
from src.templates.catalog import load_template_catalog


st.set_page_config(page_title="AI Clinic | Outgoing MTA", page_icon="📄", layout="wide")
st.html(
    """
    <style>
    html, [data-testid="stMain"] {
        scroll-behavior: smooth;
    }
    @media (prefers-reduced-motion: reduce) {
        html, [data-testid="stMain"] {
            scroll-behavior: auto;
        }
    }
    .st-key-preview_tools_button {
        position: fixed;
        top: 0.75rem;
        right: 8.5rem;
        width: auto;
        z-index: 1000001;
    }
    .st-key-preview_tools_button [data-testid="stPopoverButton"] {
        height: 2rem;
        min-height: 2rem;
        padding: 0 0.75rem;
        border-radius: 8px;
        color: #00274C;
        background: #FFFFFF;
    }
    [data-testid="stPopoverBody"]:has(.st-key-preview_menu_content) {
        width: max-content !important;
        min-width: 0 !important;
        max-width: calc(100vw - 2rem);
        border: 0;
        border-radius: 12px;
        padding: 0.5rem;
        background: #FFFFFF;
        color: #00274C;
    }
    .st-key-preview_menu_content [data-testid="stElementContainer"],
    .st-key-preview_menu_content [data-testid="stButton"] {
        width: 100% !important;
    }
    .st-key-preview_menu_content [data-testid="stButton"] button {
        width: 100%;
        justify-content: flex-start !important;
        text-align: left !important;
        white-space: nowrap;
        border: 0;
        border-radius: 4px;
        background: transparent;
        color: #00274C;
        padding: 0.35rem 0.5rem;
        min-height: 2rem;
    }
    .st-key-preview_menu_content [data-testid="stButton"] button > div {
        justify-content: flex-start !important;
        width: 100%;
        text-align: left;
    }
    .st-key-preview_menu_content [data-testid="stButton"] button p {
        font-family: inherit;
        font-size: 14px !important;
        font-weight: 400;
        line-height: 1.5;
        text-align: left;
        width: 100%;
        white-space: nowrap;
    }
    .st-key-preview_menu_content {
        gap: 0 !important;
    }
    .preview-menu-divider {
        height: 1px;
        background: rgba(0, 39, 76, 0.18);
        width: 100%;
        margin: 0.2rem 0;
    }
    .st-key-preview_menu_content [data-testid="stButton"] button:hover {
        background: #F5F5F5;
    }
    [data-testid="stHeader"] {
        background: #FFFFFF;
        height: 3.5rem;
    }
    .clinic-project-label {
        position: fixed;
        top: 0;
        right: 19rem;
        height: 3.5rem;
        display: flex;
        align-items: center;
        z-index: 1000000;
        color: #00274C;
        font-size: 12px;
        white-space: nowrap;
        margin-right: 1rem;
    }
    [data-testid="stAppDeployButton"],
    [data-testid="stAppDeployButton"] button {
        background-color: #00274C;
        color: #FFFFFF;
        border: 1px solid #00274C;
        border-radius: 8px;
    }
    [data-testid="stAppDeployButton"]:hover,
    [data-testid="stAppDeployButton"] button:hover {
        background-color: #12355B;
        color: #FFFFFF;
        border-color: #12355B;
    }
    @media (max-width: 640px) {
        .clinic-project-label {
            display: none;
        }
        .clinic-topbar {
            right: 18rem;
        }
        .clinic-topbar img {
            max-width: max(48px, calc(100vw - 20rem)) !important;
        }
    }
    [data-testid="stMainBlockContainer"] {
        padding-top: 3.5rem;
    }
    .clinic-topbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 33rem;
        height: 3.5rem;
        display: flex;
        align-items: center;
        padding-left: clamp(1rem, 6.25vw, 5rem);
        background: #FFFFFF;
        z-index: 999999;
    }
    /* Full-row fields match one half-width column; column fields stay within it. */
    [data-testid="stTextInput"],
    [data-testid="stTextArea"],
    [data-testid="stSelectbox"],
    [data-testid="stMultiSelect"],
    [data-testid="stNumberInput"] {
        max-width: calc((100vw - 2 * clamp(1rem, 6.25vw, 5rem) - 1rem) / 2);
    }
    @media (max-width: 640px) {
        [data-testid="stTextInput"],
        [data-testid="stTextArea"],
        [data-testid="stSelectbox"],
        [data-testid="stMultiSelect"],
        [data-testid="stNumberInput"] {
            max-width: 100%;
        }
    }
    [data-testid="stColumn"]:has(.st-key-section_nav) {
        position: sticky;
        top: 4.5rem;
        align-self: flex-start;
    }
    .st-key-section_nav {
        padding-top: 2.5rem;
    }
    .st-key-section_nav nav strong {
        display: block;
        margin-bottom: 1.25rem;
    }
    .st-key-section_nav nav a {
        display: block;
        padding: 0.65rem 0.75rem;
        color: #00274C;
        font-family: inherit;
        font-size: 14px;
        font-weight: 400;
        text-decoration: none !important;
        line-height: 1.4;
        border-radius: 8px;
        transition: background-color 120ms ease;
    }
    .st-key-section_nav nav a:hover,
    .st-key-section_nav nav a:focus-visible {
        background-color: #F5F5F5;
        text-decoration: none !important;
    }
    [data-testid="stHeading"] h3 {
        scroll-margin-top: 5rem;
        padding-top: 2.5rem;
    }
    [data-testid="stHeading"] h3#project-details {
        padding-top: 2.5rem;
    }
    @media (max-width: 640px) {
        [data-testid="stColumn"]:has(.st-key-section_nav) {
            position: static;
        }
    }
    h1, h2, h3 {
        color: #00274C !important;
    }
    .st-key-form_banner {
        background-color: #00274C;
        width: 100vw;
        max-width: 100vw;
        margin-left: calc(50% - 50vw);
        margin-top: -1rem;
        padding: 6rem clamp(1rem, 6.25vw, 5rem) 4.5rem;
        box-sizing: border-box;
    }
    .st-key-signing_preview, .st-key-processing_action,
    .st-key-agreement_description, .st-key-agreement_empty_state, .st-key-agreement_validation {
        max-width: calc((100vw - 2 * clamp(1rem, 6.25vw, 5rem) - 1rem) / 2);
        margin-top: 1.5rem;
    }
    .st-key-agreement_empty_state [data-testid="stMarkdownContainer"] p {
        font-family: inherit;
        font-size: 14px;
        font-weight: 400;
        line-height: 1.4;
        color: #00274C;
    }
    [class*="st-key-signer_group_"] {
        gap: 0.5rem !important;
        margin-bottom: 1rem;
    }
    [class*="st-key-signer_group_"] [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
    .signer-order-label {
        font-family: inherit;
        font-size: 14px;
        font-weight: 400;
        color: #00274C;
        margin-bottom: 0.5rem;
    }
    .signer-summary {
        background: #F5F5F5;
        border: 1px solid #989C97;
        border-radius: 8px;
        padding: 0.75rem;
        color: #00274C;
        font-family: inherit;
        font-size: 14px;
        font-weight: 400;
        line-height: 1.5;
        overflow-wrap: anywhere;
    }
    .signer-summary dl { margin: 0; padding: 0; }
    .signer-summary dt, .signer-summary dd {
        font-size: 14px;
        font-weight: 400;
        line-height: 1.5;
        padding: 0;
    }
    .signer-summary dt { margin: 0.75rem 0 0; }
    .signer-summary dt:first-child { margin-top: 0; }
    .signer-summary dd { margin: 0.125rem 0 0; font-weight: 700; }
    .signer-summary p {
        font-size: 14px;
        font-weight: 400;
        margin: 0.75rem 0 0;
    }
    .st-key-processing_action {
        border-top: 1px solid #989C97;
        padding-top: 1.5rem;
    }
    @media (max-width: 640px) {
        .st-key-signing_preview, .st-key-processing_action,
    .st-key-agreement_description, .st-key-agreement_empty_state, .st-key-agreement_validation {
            max-width: 100%;
        }
    }
    /* Field validation stays attached to its input, without a separate alert box. */
    [class*="st-key-field_"] [data-testid="stAlert"],
    [class*="st-key-field_"] [data-testid="stAlertContainer"],
    [class*="st-key-field_"] [data-baseweb="notification"] {
        background: transparent !important;
        border: 0 !important;
        border-radius: 0 !important;
        padding: 0 !important;
    }
    [class*="st-key-field_"] [data-testid="stAlert"] p {
        color: #D02030 !important;
        font-size: 14px;
        font-weight: 700 !important;
        margin: 0;
    }
    [class*="st-key-field_"]:has([data-testid="stAlert"]) {
        gap: 0.25rem !important;
        padding-bottom: 0.75rem;
    }
    [class*="st-key-field_"]:has([data-testid="stAlert"]) [data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }
    [class*="st-key-field_"] [data-testid="stAlert"] {
        margin: 0 !important;
    }
    .st-key-agreement_validation [data-testid="stAlert"],
    .st-key-agreement_validation [data-testid="stAlertContainer"],
    .st-key-agreement_validation [data-baseweb="notification"] {
        background: transparent !important;
        border: 0 !important;
        border-radius: 0 !important;
        padding: 0 !important;
    }
    .st-key-agreement_validation [data-testid="stAlert"] p {
        color: #D02030 !important;
        font-size: 14px;
        font-weight: 700 !important;
        margin: 0;
    }
    .st-key-agreement_empty_state {
        margin-top: 0;
    }
    .st-key-agreement_empty_state [data-testid="stAlertContainer"],
    .st-key-agreement_empty_state [data-baseweb="notification"] {
        background-color: #FFF1F2 !important;
        border: 0 !important;
    }
    .st-key-agreement_empty_state [data-testid="stMarkdownContainer"] p {
        color: #D02030 !important;
        font-size: 14px;
        font-weight: 700 !important;
    }
    .st-key-required_field_note {
        margin-top: -0.75rem;
        margin-bottom: 1.25rem;
    }
    .st-key-form_banner .banner-intro {
        color: #FFFFFF;
        max-width: 46rem;
        font-weight: 300;
        line-height: 1.6;
        margin: 1rem 0 0;
    }
    .st-key-form_banner h1 {
        color: #FFFFFF !important;
        padding: 0 !important;
    }
    .st-key-form_banner [data-testid="stCaptionContainer"] p {
        color: #FFFFFF !important;
    }
    </style>
    """
)

SIGNING_PREVIEW = st.query_params.get("preview") == "signing"
PREVIEW_VALUES = {
    "contact_pi_name": "Dr. Alex Morgan",
    "recipient_scientist_name": "Dr. Taylor Chen",
    "recipient_scientist_email": "taylor.chen@example.org",
    "provider_scientist_email": "alex.morgan@example.org",
    "recipient_authorized_official_name": "Jordan Lee",
    "recipient_authorized_official_title": "Research Agreements Director",
    "recipient_authorized_official_email": "jordan.lee@example.org",
    "recipient_entity": "Example Research University",
}

ANSWER_OPTIONS = ("Not answered", "Yes", "No")
ANSWER_VALUES = {"Not answered": None, "Yes": True, "No": False}
field_error_slots: dict[str, object] = {}


def signnow_secrets() -> Mapping[str, object]:
    try:
        values = st.secrets.get("signnow", {})
    except FileNotFoundError:
        return {}
    return values if isinstance(values, Mapping) else {}

BOOLEAN_FIELD_IDS = {
    "paying_for_material_as_product_or_service",
    "measurable_personnel_effort",
    "radioactive",
    "dangerous_to_handle_store_or_use",
    "hazardous_chemical_capacity_constraint",
    "will_deposit_in_repository",
    "leaving_country",
    "export_controlled",
    "return_required",
    "previously_invention_report_or_licensed",
    "external_funding_supported_development",
    "managed_affiliate_work",
    "made_using_third_party_materials",
    "clinical_health_data_shared",
    "recipient_pays_shipping",
    "material_provided_at_no_cost",
    "recipient_scientist_can_certify_organization",
}

MISSING_FIELD_MESSAGES = {
    "project_title": "Enter the project title.",
    "contact_pi_name": "Enter the Contact PI's full name.",
    "primary_research_administrator_name": (
        "Enter the Primary Research Administrator's full name."
    ),
    "material_types": "Select at least one material type.",
    "expected_duration": "Enter an expected duration greater than zero.",
    "project_administrative_home": "Enter the Project Administrative Home.",
    "recipient_entity": "Enter the Recipient Entity.",
    "recipient_scientist_name": "Enter the Recipient Scientist's full name.",
    "recipient_scientist_email": "Enter the Recipient Scientist's email address.",
    "reimbursement_cost_or_fee": (
        "Enter the reimbursement or fee, or enter None if there is none."
    ),
    "recipient_experimental_plan": (
        "Describe the Recipient's experimental plan for the material."
    ),
    "human_derived_description": "Describe the human-derived material.",
    "human_data_classification": "Enter the material classification.",
    "irb_study_number": "Enter the IRB study HUM number.",
    "protocol_consent_transfer_sections": (
        "Enter the protocol and consent sections that allow transfer outside U-M."
    ),
    "innovation_partnerships_file_number": (
        "Enter the Innovation Partnerships File Number."
    ),
    "recipient_institution_address": "Enter the Recipient Organization address.",
    "provider_scientist_email": "Enter the Provider Scientist's signing email.",
    "material_description": "Describe the material for the agreement.",
    "shipping_recipient_name": "Enter the shipping recipient's name.",
    "shipping_address": "Enter the shipping address.",
    "recipient_authorized_official_name": (
        "Enter the Recipient Authorized Official or Signatory's full name."
    ),
    "recipient_authorized_official_title": (
        "Enter the Recipient Authorized Official or Signatory's title."
    ),
    "recipient_authorized_official_email": (
        "Enter the Recipient Authorized Official or Signatory's signing email."
    ),
}

ERROR_SLOT_ALIASES = {
    "recipient_institution_name": "recipient_entity",
    "provider_scientist_name": "contact_pi_name",
    "recipient_research_purpose": "recipient_experimental_plan",
    "requested_duration": "expected_duration",
}


def required_label(label: str) -> str:
    return f"{label} *"


def error_slot(field_id: str) -> None:
    field_error_slots[field_id] = st.empty()


def show_inline_issues(
    missing_fields: list[str],
    validation_errors: dict[str, str],
    displayed_fields: set[str],
) -> None:
    for field_id in missing_fields:
        slot_id = ERROR_SLOT_ALIASES.get(field_id, field_id)
        if slot_id in displayed_fields:
            continue
        slot = field_error_slots.get(slot_id)
        if slot is None:
            continue
        message = (
            "Select Yes or No."
            if field_id in BOOLEAN_FIELD_IDS
            else MISSING_FIELD_MESSAGES.get(
                field_id, "Complete this required field."
            )
        )
        slot.error(message)
        displayed_fields.add(slot_id)

    for field_id, message in validation_errors.items():
        slot_id = ERROR_SLOT_ALIASES.get(field_id, field_id)
        if slot_id in displayed_fields:
            continue
        slot = field_error_slots.get(slot_id)
        if slot is None:
            continue
        slot.error(message)
        displayed_fields.add(slot_id)


def required_text_input(label: str, field_id: str, **kwargs: object) -> str:
    kwargs.setdefault("key", field_id)
    if SIGNING_PREVIEW and field_id in PREVIEW_VALUES and field_id not in st.session_state:
        kwargs.setdefault("value", PREVIEW_VALUES[field_id])
    with st.container(key=f"field_{field_id}"):
        value = st.text_input(required_label(label), **kwargs)
        error_slot(field_id)
    return value


def validated_text_input(label: str, field_id: str, **kwargs: object) -> str:
    kwargs.setdefault("key", field_id)
    if SIGNING_PREVIEW and field_id in PREVIEW_VALUES and field_id not in st.session_state:
        kwargs.setdefault("value", PREVIEW_VALUES[field_id])
    with st.container(key=f"field_{field_id}"):
        value = st.text_input(label, **kwargs)
        error_slot(field_id)
    return value


def required_text_area(label: str, field_id: str, **kwargs: object) -> str:
    kwargs.setdefault("key", field_id)
    if SIGNING_PREVIEW and field_id in PREVIEW_VALUES and field_id not in st.session_state:
        kwargs.setdefault("value", PREVIEW_VALUES[field_id])
    with st.container(key=f"field_{field_id}"):
        value = st.text_area(required_label(label), **kwargs)
        error_slot(field_id)
    return value


def answer_input(label: str, key: str, help_text: str | None = None) -> bool | None:
    with st.container(key=f"field_{key}"):
        answer = st.selectbox(
            required_label(label), ANSWER_OPTIONS, key=key, help=help_text
        )
        error_slot(key)
    return ANSWER_VALUES[answer]


def show_check_list(title: str, items: list[dict]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption("None")
        return
    for item in items:
        st.markdown(f"- {item['label']}")


logo_path = Path(__file__).resolve().parent / "assets" / "innovation-partnerships.png"
logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
st.html(
    f'<div class="clinic-topbar"><img src="data:image/png;base64,{logo_data}" '
    'alt="Innovation Partnerships, University of Michigan" '
    'style="display:block;width:300px;max-width:100%;height:auto;'
    'border-radius:0;object-fit:contain;"></div>'
    '<span class="clinic-project-label">AI Clinic · Proof of concept</span>'
)
with st.container(key="form_banner"):
    st.title("Outgoing Material Transfer Agreement")
    st.markdown(
        '<p class="banner-intro">Request an outgoing transfer of U-M research materials. '
        'Your answers help determine eligibility for a standard MTA and prepare '
        'the agreement for signature.</p>',
        unsafe_allow_html=True,
    )
if SIGNING_PREVIEW:
    st.caption("Design preview · Sample signer details only · Nothing has been submitted.")
def load_sample_data(incomplete: bool = False) -> None:
    sample_path = Path(__file__).resolve().parent / "assets" / "sample-request.json"
    sample = json.loads(sample_path.read_text())
    values = {**sample["erpm_intake"], **sample["agreement_information"]}
    for field_id, value in values.items():
        if isinstance(value, bool):
            value = "Yes" if value else "No"
        st.session_state[field_id] = value
    st.session_state["sample_data_loaded"] = True
    st.session_state["show_sample_validation"] = incomplete
    if incomplete:
        for field_id in ("project_title", "provider_scientist_email", "recipient_institution_address"):
            st.session_state[field_id] = ""



def clear_form() -> None:
    st.session_state.clear()
    if "preview" in st.query_params:
        del st.query_params["preview"]


with st.container(key="preview_tools_button"):
    with st.popover("Preview Tools"):
        with st.container(key="preview_menu_content"):
            st.button("Load sample data", on_click=load_sample_data, width="stretch")
            st.html('<div class="preview-menu-divider"></div>')
            st.button("Load incomplete sample", on_click=load_sample_data, kwargs={"incomplete": True}, width="stretch")
            st.html('<div class="preview-menu-divider"></div>')
            st.button("Clear form", on_click=clear_form, width="stretch")
    
navigation_column, fields_column = st.columns([1, 3], gap="large")
with navigation_column:
    with st.container(key="section_nav"):
        st.html(
            '<nav aria-label="Form sections">'
            '<strong>Jump To Form Section</strong>'
            '<a href="#project-details" target="_self">Project Details</a>'
            '<a href="#personnel" target="_self">Personnel</a>'
            '<a href="#material-details" target="_self">Material Details</a>'
            '<a href="#material-safety" target="_self">Material Safety</a>'
            '<a href="#outgoing-material-details" target="_self">Outgoing Material Details</a>'
            '<a href="#agreement-and-signing-information" target="_self">Agreement and Signing Information</a>'
            '</nav>'
        )
with fields_column:
    st.subheader("Project Details", anchor="project-details")
    with st.container(key="required_field_note"):
        st.caption(r"\* indicates a required field throughout this form.")
    project_title = required_text_input("Project Title", "project_title")
    paying_for_material = answer_input(
        "Are you paying for this material as a product or a service from a company?",
        "paying_for_material_as_product_or_service",
        "This does not include paying a shipping fee.",
    )
    with st.container(key="field_expected_duration"):
        duration_years = st.number_input(
            "Expected Duration — Years *", min_value=0, step=1, value=0, key="duration_years",
            help="Enter at least one month or one year across the duration fields.",
        )
        duration_months = st.number_input(
            "Expected Duration — Months *", min_value=0, step=1, value=0, key="duration_months",
            help="Enter at least one month or one year across the duration fields.",
        )
        error_slot("expected_duration")
    duration_comments = st.text_area("Duration Comments")

    st.subheader("Personnel")
    contact_pi_name = required_text_input("Contact PI", "contact_pi_name")
    primary_ra_name = required_text_input(
        "Primary Research Administrator", "primary_research_administrator_name"
    )
    measurable_personnel_effort = answer_input(
        "Is there measurable personnel effort for the project that is related to the unfunded agreement?",
        "measurable_personnel_effort",
    )

    personnel_agreement_fields = st.container()

    st.subheader("Material Details")
    with st.container(key="field_material_types"):
        material_types = st.multiselect(
            required_label("Material Type"), options=MATERIAL_TYPES,
            default=["Chemical compound"] if SIGNING_PREVIEW else None,
            key="material_types",
        )
        error_slot("material_types")
    human_derived_description = ""
    human_data_classification = ""
    irb_study_number = ""
    protocol_consent_transfer_sections = ""
    if HUMAN_MATERIAL_TYPE in material_types:
        human_derived_description = required_text_area(
            "Human derived tissue/samples description", "human_derived_description"
        )
        human_data_classification = required_text_area(
            "How are these materials classified?", "human_data_classification"
        )
        irb_study_number = required_text_input(
            "IRB study HUM number", "irb_study_number"
        )
        protocol_consent_transfer_sections = required_text_area(
            "Protocol and informed-consent sections allowing transfer outside U-M",
            "protocol_consent_transfer_sections",
        )

    material_agreement_fields = st.container()

    st.subheader("Material Safety")
    radioactive = answer_input("Are any of the materials radioactive?", "radioactive")
    dangerous_to_handle = answer_input(
        "Are materials dangerous to handle, store, or use?",
        "dangerous_to_handle_store_or_use",
    )
    hazardous_chemical_capacity_constraint = answer_input(
        "Is this a hazardous chemical that has a capacity constraint?",
        "hazardous_chemical_capacity_constraint",
    )

    st.subheader("Outgoing Material Details")
    st.markdown("#### Required")
    project_administrative_home = required_text_input(
        "Project Administrative Home", "project_administrative_home"
    )
    will_deposit_in_repository = answer_input(
        "Will the material be deposited in a repository?", "will_deposit_in_repository"
    )

    recipient_entity = required_text_input(
        "Recipient Entity full name",
        "recipient_entity",
        help=(
            "Enter the recipient's complete institution or organization name. "
            "For a university department, include the university name; for example, "
            "Department of Chemistry, University of Michigan."
        ),
    )
    recipient_scientist_name = required_text_input(
        "Recipient Scientist Name", "recipient_scientist_name"
    )
    recipient_scientist_email = required_text_input(
        "Recipient Scientist Email", "recipient_scientist_email"
    )
    leaving_country = answer_input(
        "Is material, data, equipment, or software leaving the country?",
        "leaving_country",
    )
    export_controlled = answer_input(
        "Are you shipping export-controlled materials, data, equipment, or software?",
        "export_controlled",
    )
    reimbursement_cost_or_fee = required_text_input(
        "What reimbursement cost or fee, if any, will U-M request from the recipient?",
        "reimbursement_cost_or_fee",
        help="Enter None if U-M will not request a reimbursement or fee.",
    )
    experimental_plan = required_text_area(
        "Recipient's experimental plan for use of the material",
        "recipient_experimental_plan",
        help="Brief description, limited to 200 words.",
    )
    return_required = answer_input(
        "Is the recipient required to send anything in return for the material?",
        "return_required",
    )
    previously_invention_report_or_licensed = answer_input(
        "Were these materials previously described in a U-M invention report or licensed by U-M?",
        "previously_invention_report_or_licensed",
    )
    innovation_partnerships_file_number = ""
    if previously_invention_report_or_licensed is True:
        innovation_partnerships_file_number = required_text_input(
            "Innovation Partnerships File Number",
            "innovation_partnerships_file_number",
        )
    external_funding_supported_development = answer_input(
        "Did an externally funded project support development of the material?",
        "external_funding_supported_development",
    )
    managed_affiliate_work = answer_input(
        "Will U-M employees perform any work at a location on the Managed Affiliates list?",
        "managed_affiliate_work",
    )
    made_using_third_party_materials = answer_input(
        "Were these materials made using materials received from another party or a commercial purchase?",
        "made_using_third_party_materials",
    )
    clinical_health_data_shared = answer_input(
        "Will clinical health data be shared outside the University of Michigan?",
        "clinical_health_data_shared",
    )
    outgoing_agreement_fields = st.container()

    st.markdown("#### Optional")
    recipient_admin_name = st.text_input("Recipient Administrative Contact Name")
    recipient_admin_email = validated_text_input(
        "Recipient Administrative Contact Email",
        "recipient_administrative_contact_email",
    )
    recipient_admin_street_address = st.text_input(
        "Recipient Administrative Contact Street Address"
    )
    recipient_admin_telephone = st.text_input(
        "Recipient Administrative Contact Telephone"
    )
    recipient_admin_fax = st.text_input("Recipient Administrative Contact Fax")

    related_details = st.text_area(
        "Other Relevant Details", key="related_details",
        help="Optional supporting details can help resolve screening questions.",
    )

    selected_categories = derive_material_categories(material_types)
    selected_category = selected_categories[0] if len(selected_categories) == 1 else None
    template_candidates = [
        definition.template_id
        for definition in load_template_catalog()
        if definition.automation_enabled
        and isinstance(selected_category, str)
        and selected_category in definition.material_categories
    ]
    selected_template_id = (
        template_candidates[0] if len(template_candidates) == 1 else None
    )

    provider_scientist_title = ""
    provider_scientist_email = ""
    recipient_scientist_title = ""
    recipient_institution_address = ""
    material_description = ""
    shipping_recipient_name = ""
    shipping_address = ""
    recipient_scientist_can_certify: bool | None = None
    recipient_official_name = ""
    recipient_official_title = ""
    recipient_official_email = ""

    recipient_pays_shipping: bool | None = None
    material_provided_at_no_cost: bool | None = None
    if selected_template_id is not None:
        with personnel_agreement_fields:
            provider_scientist_title = st.text_input(
                "Provider Scientist academic/job title (if known)"
            )
            provider_scientist_email = required_text_input(
                "Provider Scientist signing email",
                "provider_scientist_email",
                help="Used to deliver the signing request; it is not printed in the agreement.",
            )
            if selected_template_id != "device_material_agreement":
                recipient_scientist_title = st.text_input(
                    "Recipient Scientist academic/job title (if known)"
                )
        with outgoing_agreement_fields:
            recipient_institution_address = required_text_area(
                "Recipient Organization address", "recipient_institution_address"
            )
        with material_agreement_fields:
            material_label = (
                "Original Material description"
                if selected_category == "biological"
                else "Material description"
            )
            material_description = required_text_area(
                material_label, "material_description"
            )

        with outgoing_agreement_fields:
            recipient_pays_shipping = answer_input(
                "Will the Recipient Scientist pay the shipping costs?",
                "recipient_pays_shipping",
            )
            material_provided_at_no_cost = answer_input(
                "Will the Provider Scientist provide the materials at no cost?",
                "material_provided_at_no_cost",
                "A preparation or distribution reimbursement entered above is still allowed.",
            )

            if selected_template_id in {"chemical_material_agreement", "animal_material_agreement"}:
                shipping_recipient_name = required_text_input(
                    "Shipping recipient name", "shipping_recipient_name"
                )
                shipping_address = required_text_area(
                    "Shipping address", "shipping_address"
                )

            if selected_template_id == "biological_material_agreement":
                recipient_scientist_can_certify = answer_input(
                    "Recipient Scientist authorized to certify for Recipient Organization?",
                    "recipient_scientist_can_certify_organization",
                )

        preview_information: dict[str, object] = {
            "provider_scientist_name": contact_pi_name,
            "provider_scientist_title": provider_scientist_title,
            "provider_scientist_email": provider_scientist_email,
            "recipient_scientist_name": recipient_scientist_name,
            "recipient_scientist_title": recipient_scientist_title,
            "recipient_scientist_email": recipient_scientist_email,
            "recipient_scientist_can_certify_organization": (
                recipient_scientist_can_certify
            ),
        }
        preview_plan = build_signer_plan(
            selected_template_id, preview_information, strict=False
        )
        official_signer = next(
            (
                signer
                for signer in preview_plan.signers
                if signer.party == "recipient_authorized_official"
            ),
            None,
        )
        if official_signer is not None:
            with outgoing_agreement_fields:
                official_role = official_signer.label
                recipient_official_name = required_text_input(
                    f"{official_role} name", "recipient_authorized_official_name"
                )
                recipient_official_title = required_text_input(
                    f"{official_role} title", "recipient_authorized_official_title"
                )
                recipient_official_email = required_text_input(
                    f"{official_role} signing email",
                    "recipient_authorized_official_email",
                    help="Used to deliver the signing request; it is not printed in the agreement.",
                )

            preview_information.update(
                {
                    "recipient_authorized_official_name": recipient_official_name,
                    "recipient_authorized_official_title": recipient_official_title,
                    "recipient_authorized_official_email": recipient_official_email,
                }
            )
            preview_plan = build_signer_plan(
                selected_template_id, preview_information, strict=False
            )

    st.subheader("Agreement and Signing Information")
    erpm_intake = {
        "project_title": project_title,
        "paying_for_material_as_product_or_service": paying_for_material,
        "duration_years": duration_years,
        "duration_months": duration_months,
        "duration_comments": duration_comments,
        "contact_pi_name": contact_pi_name,
        "primary_research_administrator_name": primary_ra_name,
        "measurable_personnel_effort": measurable_personnel_effort,
        "material_types": material_types,
        "human_derived_description": human_derived_description,
        "human_data_classification": human_data_classification,
        "irb_study_number": irb_study_number,
        "protocol_consent_transfer_sections": protocol_consent_transfer_sections,
        "radioactive": radioactive,
        "dangerous_to_handle_store_or_use": dangerous_to_handle,
        "hazardous_chemical_capacity_constraint": hazardous_chemical_capacity_constraint,
        "project_administrative_home": project_administrative_home,
        "will_deposit_in_repository": will_deposit_in_repository,
        "recipient_entity": recipient_entity,
        "recipient_scientist_name": recipient_scientist_name,
        "recipient_scientist_email": recipient_scientist_email,
        "recipient_administrative_contact_name": recipient_admin_name,
        "recipient_administrative_contact_email": recipient_admin_email,
        "recipient_administrative_contact_street_address": recipient_admin_street_address,
        "recipient_administrative_contact_telephone": recipient_admin_telephone,
        "recipient_administrative_contact_fax": recipient_admin_fax,
        "leaving_country": leaving_country,
        "export_controlled": export_controlled,
        "reimbursement_cost_or_fee": reimbursement_cost_or_fee,
        "recipient_experimental_plan": experimental_plan,
        "return_required": return_required,
        "previously_invention_report_or_licensed": previously_invention_report_or_licensed,
        "innovation_partnerships_file_number": innovation_partnerships_file_number,
        "external_funding_supported_development": external_funding_supported_development,
        "managed_affiliate_work": managed_affiliate_work,
        "made_using_third_party_materials": made_using_third_party_materials,
        "clinical_health_data_shared": clinical_health_data_shared,
        "related_document_names": [],
        "related_details": related_details,
    }
    agreement_information: dict[str, object] = {}
    if selected_template_id is not None:
        agreement_information.update(
            {
                "recipient_institution_address": recipient_institution_address,
                "provider_scientist_title": provider_scientist_title,
                "provider_scientist_email": provider_scientist_email,
                "material_description": material_description,
                "recipient_pays_shipping": recipient_pays_shipping,
                "material_provided_at_no_cost": material_provided_at_no_cost,
            }
        )
    if selected_template_id is not None and selected_template_id != "device_material_agreement":
        agreement_information["recipient_scientist_title"] = recipient_scientist_title
    if selected_template_id in {"chemical_material_agreement", "animal_material_agreement"}:
        agreement_information.update(
            {
                "shipping_recipient_name": shipping_recipient_name,
                "shipping_address": shipping_address,
            }
        )
    if selected_template_id == "biological_material_agreement":
        agreement_information[
            "recipient_scientist_can_certify_organization"
        ] = recipient_scientist_can_certify
    if recipient_official_name or recipient_official_title or recipient_official_email:
        agreement_information.update(
            {
                "recipient_authorized_official_name": recipient_official_name,
                "recipient_authorized_official_title": recipient_official_title,
                "recipient_authorized_official_email": recipient_official_email,
            }
        )

    request = {
        "erpm_intake": erpm_intake,
        "agreement_information": agreement_information,
    }

    intake_check = evaluate_intake_readiness(request)
    agreement_check = evaluate_agreement_readiness(request, template_id=selected_template_id)
    review_complete = (
        selected_template_id is not None
        and intake_check["status"] == "ready"
        and agreement_check["status"] == "ready"
    )
    if review_complete:
        with st.container(key="signing_preview"):
            st.markdown("#### Signing Preview")
            st.caption(
                "Review who will sign and in what order. Signing email addresses are not printed in the agreement."
            )
            if preview_plan.decision_required:
                st.caption(
                    "Answer whether the Recipient Scientist can certify for the Recipient Organization above to see the signing order."
                )
            else:
                for signer in preview_plan.signers:
                    with st.container(key=f"signer_group_{signer.party}"):
                        st.html(
                            f'<div class="signer-order-label">Signing order {signer.order}</div>'
                            '<section class="signer-summary" aria-label="Signing order '
                            f'{signer.order}">'
                            '<dl>'
                            f'<dt>Role</dt><dd>{escape(signer.label)}</dd>'
                            f'<dt>Name</dt><dd>{escape(signer.name or "Not entered")}</dd>'
                            f'<dt>Email</dt><dd>{escape(signer.email or "Not entered")}</dd>'
                            '</dl>'
                            '</section>'
                        )
                        st.caption(
                            "From Personnel" if signer.party == "provider_scientist"
                            else "From Outgoing Material Details"
                        )
    else:
        with st.container(key="agreement_empty_state"):
            st.info("Please recheck the form and complete the required fields above to review the signing information.")

    project_root = Path(__file__).resolve().parent
    agreement_sender, signing_mode = build_agreement_sender(
        project_root, signnow_secrets()
    )
    with st.container(key="processing_action"):
        if signing_mode == "signnow_development":
            st.caption(
                "SignNow test mode: eligible agreements will be sent to the listed signers."
            )
        else:
            st.caption(
                "Local preview: creates an agreement and signing package. No emails will be sent."
            )

        submitted = st.button("Process request", type="primary")

    if submitted or st.session_state.get("show_sample_validation", False):
        issue_ids = set()
        for readiness in (intake_check, agreement_check):
            issue_ids.update(readiness["missing_fields"])
            issue_ids.update(readiness["validation_errors"])
        if issue_ids:
            selectors = []
            for field_id in issue_ids:
                slot_id = ERROR_SLOT_ALIASES.get(field_id, field_id)
                if slot_id not in field_error_slots:
                    continue
                prefix = f".st-key-field_{slot_id}"
                selectors.extend([
                    f"{prefix} input",
                    f'{prefix} [data-baseweb="input"]',
                    f'{prefix} [data-testid="stTextInputRootElement"]',
                    f'{prefix} [data-testid="stTextAreaRootElement"]',
                    f'{prefix} [data-baseweb="textarea"]',
                    f"{prefix} textarea",
                    f'{prefix} [data-baseweb="select"] > div',
                ])
            if selectors:
                st.html(
                    "<style>" + ",".join(selectors)
                    + "{border-color: #D02030 !important;}"
                    + "</style>"
                )

        displayed_fields: set[str] = set()
        show_inline_issues(
            intake_check["missing_fields"],
            intake_check["validation_errors"],
            displayed_fields,
        )
        show_inline_issues(
            agreement_check["missing_fields"],
            agreement_check["validation_errors"],
            displayed_fields,
        )

    if submitted:
        report = build_screening_report(request)
        intake_readiness = report["intake_readiness"]
        eligibility = report["eligibility"]
        agreement_readiness = report["agreement_readiness"]
        template_result = report["template_selection"]

        if (
            "Provider material is not supplied at no cost."
            in agreement_readiness["review_reasons"]
        ):
            no_cost_slot = field_error_slots.get("material_provided_at_no_cost")
            if no_cost_slot is not None:
                no_cost_slot.warning(
                    "This answer is complete, but it requires manual special-case review "
                    "because the standard agreement templates are for no-cost transfers "
                    "apart from permitted preparation, distribution, or shipping charges."
                )

        st.divider()
        st.header("Processing Result")
        if intake_readiness["status"] == "ready":
            st.success("Requester questionnaire is complete.")
        else:
            st.warning(
                "Requester questionnaire is incomplete: "
                + ", ".join(intake_readiness["missing_fields"])
            )

        if eligibility["status"] == "eligible":
            st.success("Eligible for Standard MTA automatic approval under the checklist.")
        elif eligibility["status"] == "ineligible":
            st.error(
                "Not eligible for Standard MTA automatic approval; "
                "manual special-case review is required."
            )
        else:
            st.warning(
                "Eligibility is unresolved; manual special-case review is required."
            )
        st.write(eligibility["explanation"])

        result_left, result_right = st.columns(2)
        with result_left:
            show_check_list("Passed checks", eligibility["passed_checks"])
            show_check_list("Failed checks", eligibility["failed_checks"])
        with result_right:
            show_check_list("Unanswered checks", eligibility["missing_information"])
            st.markdown("**Agreement information**")
            st.write(agreement_readiness["status"].replace("_", " ").title())
            if agreement_readiness["missing_fields"]:
                st.write("Missing: " + ", ".join(agreement_readiness["missing_fields"]))
            if agreement_readiness["validation_errors"]:
                for message in agreement_readiness["validation_errors"].values():
                    st.write(message)

        st.markdown("**Template decision**")
        if template_result["selected_template"]:
            selected_id = template_result["selected_template"]
            selected_detail = next(
                detail
                for detail in template_result["candidate_details"]
                if detail["template_id"] == selected_id
            )
            st.success("Selected template: " + selected_detail["display_name"])
        else:
            for reason in template_result["review_reasons"]:
                st.caption(reason)

        pipeline = OutgoingMTAPipeline(
            renderer=DocxAgreementRenderer(project_root / "outputs" / "agreements"),
            sender=agreement_sender,
        )
        pipeline_result = pipeline.run(request)

        st.markdown("**Automation result**")
        if pipeline_result.status in {"prepared_for_signature", "sent_for_signature"}:
            if pipeline_result.status == "sent_for_signature":
                st.success("Agreement sent through SignNow Development Mode.")
                st.caption(
                    "SignNow document ID: "
                    + (pipeline_result.delivery_reference or "Unavailable")
                )
            else:
                st.success("Agreement and local SignNow package are ready.")
            agreement_path = Path(pipeline_result.artifact_path or "")
            manifest_path = Path(pipeline_result.delivery_reference or "")
            if agreement_path.is_file():
                st.download_button(
                    "Download final agreement for signing",
                    data=agreement_path.read_bytes(),
                    file_name=agreement_path.name,
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                )
            if pipeline_result.delivery_mode == "signnow_package" and manifest_path.is_file():
                st.download_button(
                    "Download signing manifest",
                    data=manifest_path.read_text(encoding="utf-8"),
                    file_name=manifest_path.name,
                    mime="application/json",
                )
        elif pipeline_result.status == "intake_incomplete":
            st.warning("Complete the requester questionnaire and process it again.")
        elif pipeline_result.status == "agreement_incomplete":
            st.warning("Complete the agreement and signing information and process it again.")
        elif pipeline_result.status == "manual_special_case_review":
            st.warning("This request requires manual special-case MTA review in eRPM.")
        else:
            st.error("Automatic processing stopped: " + "; ".join(pipeline_result.reasons))

        st.download_button(
            "Download screening report",
            data=serialize_screening_report(report),
            file_name="mta_screening_report.json",
            mime="application/json",
        )
