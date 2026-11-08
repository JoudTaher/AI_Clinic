from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import streamlit as st

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


st.set_page_config(page_title="Outgoing MTA Screening PoC", page_icon="📄", layout="wide")
st.html(
    """
    <style>
    h1, h2, h3 {
        color: #FFCB05 !important;
    }
    </style>
    """
)

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
    value = st.text_input(required_label(label), **kwargs)
    error_slot(field_id)
    return value


def validated_text_input(label: str, field_id: str, **kwargs: object) -> str:
    value = st.text_input(label, **kwargs)
    error_slot(field_id)
    return value


def required_text_area(label: str, field_id: str, **kwargs: object) -> str:
    value = st.text_area(required_label(label), **kwargs)
    error_slot(field_id)
    return value


def answer_input(label: str, key: str, help_text: str | None = None) -> bool | None:
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


st.title("Outgoing MTA Automation Proof of Concept")
st.caption("Questionnaire → backend eligibility rules → agreement → signing package")
st.write(
    "The requester questionnaire follows the supplied outgoing MTA form. "
    "The supplied eligibility checklist runs only in the backend."
)
st.caption("* Required field")

st.subheader("Introduction")
st.caption("Agreement Category: Material Transfer Agreement · Agreement Type: Outgoing MTA")
intro_left, intro_right = st.columns(2)
with intro_left:
    project_title = required_text_input("Project Title", "project_title")
    paying_for_material = answer_input(
        "Are you paying for this material as a product or a service from a company?",
        "paying_for_material_as_product_or_service",
        "This does not include paying a shipping fee.",
    )
with intro_right:
    duration_years = st.number_input(
        "Expected Duration — Years *", min_value=0, step=1, value=0,
        help="Enter at least one month or one year across the duration fields.",
    )
    duration_months = st.number_input(
        "Expected Duration — Months *", min_value=0, step=1, value=0,
        help="Enter at least one month or one year across the duration fields.",
    )
    error_slot("expected_duration")
    duration_comments = st.text_area("Duration Comments")

st.subheader("Personnel")
personnel_left, personnel_right = st.columns(2)
with personnel_left:
    contact_pi_name = required_text_input("Contact PI", "contact_pi_name")
with personnel_right:
    primary_ra_name = required_text_input(
        "Primary Research Administrator", "primary_research_administrator_name"
    )
measurable_personnel_effort = answer_input(
    "Is there measurable personnel effort for the project that is related to the unfunded agreement?",
    "measurable_personnel_effort",
)

st.subheader("Material Details")
material_types = st.multiselect(required_label("Material Type"), options=MATERIAL_TYPES)
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

st.subheader("Material Safety")
safety_left, safety_middle, safety_right = st.columns(3)
with safety_left:
    radioactive = answer_input("Are any of the materials radioactive?", "radioactive")
with safety_middle:
    dangerous_to_handle = answer_input(
        "Are materials dangerous to handle, store, or use?",
        "dangerous_to_handle_store_or_use",
    )
with safety_right:
    hazardous_chemical_capacity_constraint = answer_input(
        "Is this a hazardous chemical that has a capacity constraint?",
        "hazardous_chemical_capacity_constraint",
    )

st.subheader("Outgoing Material Details")
project_administrative_home = required_text_input(
    "Project Administrative Home", "project_administrative_home"
)
will_deposit_in_repository = answer_input(
    "Will the material be deposited in a repository?", "will_deposit_in_repository"
)

recipient_left, recipient_right = st.columns(2)
with recipient_left:
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
with recipient_right:
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
related_documents = st.file_uploader(
    "Related Documents", accept_multiple_files=True
)
related_details = st.text_area("Other Relevant Details")

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

st.subheader("Agreement and Signing Information")
st.caption(
    "These are the population and signer fields in the agreement selected by the "
    "material type. Names, organization, research purpose, duration, and fee entered "
    "above are reused."
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
    name_left, name_right = st.columns(2)
    with name_left:
        st.caption(
            "Provider Scientist full name: "
            f"{contact_pi_name or 'Not entered above'} (from Contact PI)"
        )
    with name_right:
        st.caption(
            "Recipient Scientist: "
            f"{recipient_scientist_name or 'Not entered above'} · "
            f"{recipient_scientist_email or 'email not entered above'} "
            "(reused from Outgoing Material Details)"
        )

    agreement_left, agreement_right = st.columns(2)
    with agreement_left:
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
    with agreement_right:
        recipient_institution_address = required_text_area(
            "Recipient Organization address", "recipient_institution_address"
        )
        material_label = (
            "Original Material description"
            if selected_category == "biological"
            else "Material description"
        )
        material_description = required_text_area(
            material_label, "material_description"
        )

    terms_left, terms_right = st.columns(2)
    with terms_left:
        recipient_pays_shipping = answer_input(
            "Will the Recipient Scientist pay the shipping costs?",
            "recipient_pays_shipping",
        )
    with terms_right:
        material_provided_at_no_cost = answer_input(
            "Will the Provider Scientist provide the materials at no cost?",
            "material_provided_at_no_cost",
            "A preparation or distribution reimbursement entered above is still allowed.",
        )

    if selected_template_id in {"chemical_material_agreement", "animal_material_agreement"}:
        shipping_left, shipping_right = st.columns(2)
        with shipping_left:
            shipping_recipient_name = required_text_input(
                "Shipping recipient name", "shipping_recipient_name"
            )
        with shipping_right:
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
        official_role = official_signer.label
        official_left, official_middle, official_right = st.columns(3)
        with official_left:
            recipient_official_name = required_text_input(
                f"{official_role} name", "recipient_authorized_official_name"
            )
        with official_middle:
            recipient_official_title = required_text_input(
                f"{official_role} title", "recipient_authorized_official_title"
            )
        with official_right:
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

    st.markdown("**Planned SignNow invitations**")
    st.caption(
        "The configured SignNow developer account sends the invitations. The email "
        "addresses below are recipients; signing emails are not printed in the agreement."
    )
    if preview_plan.decision_required:
        st.caption(
            "Select whether the Recipient Scientist can certify for the Recipient "
            "Organization to determine the final recipient signer plan."
        )
    else:
        for signer in preview_plan.signers:
            st.caption(
                f"Signing order {signer.order} — {signer.label}: "
                f"{signer.name or 'name not entered'} "
                f"<{signer.email or 'email not entered'}> "
                f"({signer.source_summary})."
            )
else:
    st.info(
        "Select exactly one supported material category to show the matching agreement fields."
    )

project_root = Path(__file__).resolve().parent
agreement_sender, signing_mode = build_agreement_sender(
    project_root, signnow_secrets()
)
if signing_mode == "signnow_development":
    st.caption(
        "Signing delivery: SignNow Development Mode. Eligible agreements will be "
        "uploaded and sent to the listed signers."
    )
else:
    st.caption(
        "Signing delivery: local test package. No email or SignNow API request will be sent."
    )

submitted = st.button("Process request", type="primary")

if submitted:
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
        "related_document_names": [document.name for document in related_documents],
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

    report = build_screening_report(request)
    intake_readiness = report["intake_readiness"]
    eligibility = report["eligibility"]
    agreement_readiness = report["agreement_readiness"]
    template_result = report["template_selection"]

    displayed_fields: set[str] = set()
    show_inline_issues(
        intake_readiness["missing_fields"],
        intake_readiness["validation_errors"],
        displayed_fields,
    )
    show_inline_issues(
        agreement_readiness["missing_fields"],
        agreement_readiness["validation_errors"],
        displayed_fields,
    )
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
