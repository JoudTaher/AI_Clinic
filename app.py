from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.adapters.docx_renderer import DocxAgreementRenderer
from src.adapters.signnow_package_sender import SignNowPackageSender
from src.eligibility import CATEGORY_TO_SECTION, SECTION_CRITERIA
from src.pipeline.outgoing_mta import OutgoingMTAPipeline
from src.screening_report import build_screening_report, serialize_screening_report
from src.signing.config import SigningConfiguration, SigningConfigurationError


st.set_page_config(page_title="Outgoing MTA Screening PoC", page_icon="📄", layout="wide")

ANSWER_OPTIONS = ("Unknown", "Yes", "No")
ANSWER_VALUES = {"Unknown": None, "Yes": True, "No": False}

MATERIAL_TYPES = (
    "Human derived materials (isolated tissue, samples, specimens, cells, etc.)",
    "Cells (other than those derived from human subjects or patients)",
    "Plasmid/vector (DNA or RNA)",
    "Mouse/Rat",
    "Other model organism (yeast, drosophila, zebrafish)",
    "Custom antibody",
    "Protein",
    "Chemical compound",
    "Software/code",
    "Device",
    "Other material",
)

MATERIAL_TYPE_TO_CATEGORY = {
    MATERIAL_TYPES[0]: "biological",
    MATERIAL_TYPES[1]: "biological",
    MATERIAL_TYPES[2]: "biological",
    MATERIAL_TYPES[3]: "animal_derived",
    MATERIAL_TYPES[4]: "biological",
    MATERIAL_TYPES[5]: "biological",
    MATERIAL_TYPES[6]: "biological",
    MATERIAL_TYPES[7]: "chemical",
    MATERIAL_TYPES[8]: "other",
    MATERIAL_TYPES[9]: "device",
    MATERIAL_TYPES[10]: "other",
}

SECTION_TITLES = {
    "A": "General eligibility",
    "B": "Chemical materials",
    "C": "Biological materials",
    "D": "Devices",
    "E": "Animal materials",
}


def answer_input(label: str, key: str, help_text: str | None = None) -> bool | None:
    answer = st.selectbox(label, ANSWER_OPTIONS, key=key, help=help_text)
    return ANSWER_VALUES[answer]


def tri_state_input(label: str, field_id: str) -> bool | None:
    return answer_input(
        label,
        key=f"eligibility_{field_id}",
        help_text="Choose Yes only when the checklist statement is confirmed true.",
    )


def show_check_list(title: str, items: list[dict]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption("None")
        return
    for item in items:
        st.markdown(f"- {item['label']}  \n  `[{item['field_id']}]`")


st.title("Outgoing MTA Automation Proof of Concept")
st.caption("Automatic standard-request routing · Local SignNow package · No network send")
st.write(
    "This intake follows the sections and field names in the submitted outgoing "
    "MTA eRPM worksheet. Standard requests are processed automatically; all other "
    "requests route to eRPM."
)

st.subheader("Introduction")
request_id = st.text_input("Request ID")
intro_left, intro_right = st.columns(2)
with intro_left:
    project_title = st.text_input("Project title")
    st.text_input("Agreement category", value="Material Transfer Agreement", disabled=True)
    st.text_input("Agreement type", value="Outgoing MTA", disabled=True)
    paying_um_for_material = answer_input(
        "Are you paying U-M for this material as a product or service from a company?",
        "paying_um_for_material",
        "Do not count a shipping fee as payment for the material.",
    )
with intro_right:
    duration_years = st.number_input(
        "Expected duration — years", min_value=0, step=1, value=0
    )
    duration_months = st.number_input(
        "Expected duration — months", min_value=0, step=1, value=0
    )
    duration_comments = st.text_area("Duration comments")
    copy_from_existing_ufa = answer_input(
        "Copy data from an existing UFA record?", "copy_from_existing_ufa"
    )

st.subheader("Personnel")
personnel_left, personnel_right = st.columns(2)
with personnel_left:
    contact_pi_name = st.text_input("Contact PI name")
    contact_pi_title = st.text_input("U-M provider scientist title")
    contact_pi_phone = st.text_input("Contact PI phone")
    contact_pi_email = st.text_input("Contact PI email")
with personnel_right:
    primary_ra_name = st.text_input("Primary Research Administrator name")
    primary_ra_phone = st.text_input("Primary Research Administrator phone")
    primary_ra_email = st.text_input("Primary Research Administrator email")
measurable_personnel_effort = answer_input(
    "Is there measurable personnel effort related to the unfunded agreement?",
    "measurable_personnel_effort",
)

st.subheader("Material Details")
material_types = st.multiselect("Material types", options=MATERIAL_TYPES)
material_description = st.text_area("Plasmid/Vector/DNA/RNA description")

st.subheader("Material Safety")
safety_left, safety_middle, safety_right = st.columns(3)
with safety_left:
    radioactive = answer_input(
        "Are any of the materials radioactive?", "radioactive"
    )
with safety_middle:
    dangerous_to_handle = answer_input(
        "Are materials dangerous to handle, store, or use?", "dangerous_to_handle"
    )
with safety_right:
    hazardous_chemical_capacity_constraint = answer_input(
        "Is this a hazardous chemical that has a capacity constraint?",
        "hazardous_chemical_capacity_constraint",
    )

st.subheader("Outgoing Material Details")
project_administrative_home = st.text_input("Project Administrative Home")
will_deposit_in_repository = answer_input(
    "Will material be deposited in a repository?", "will_deposit_in_repository"
)

recipient_left, recipient_right = st.columns(2)
with recipient_left:
    recipient_entity = st.text_input("Recipient entity")
    recipient_scientist_name = st.text_input("Recipient scientist name")
    recipient_scientist_title = st.text_input("Recipient scientist title")
    recipient_scientist_email = st.text_input("Recipient scientist email")
with recipient_right:
    recipient_admin_name = st.text_input("Recipient administrative contact name")
    recipient_admin_email = st.text_input("Recipient administrative contact email")
    recipient_admin_street_address = st.text_input(
        "Recipient administrative contact street address"
    )
    recipient_admin_telephone = st.text_input(
        "Recipient administrative contact telephone"
    )
    recipient_admin_fax = st.text_input("Recipient administrative contact fax")

shipping_left, shipping_right = st.columns(2)
with shipping_left:
    shipping_recipient_name = st.text_input("Shipping recipient name")
with shipping_right:
    shipping_address = st.text_input("Shipping address")

st.markdown("#### Recipient signing information")
recipient_scientist_can_certify = answer_input(
    "Is the recipient scientist authorized to certify for the recipient organization?",
    "recipient_scientist_can_certify",
    "This determines whether the UBMTA needs a separate recipient organization certifier.",
)
official_left, official_middle, official_right = st.columns(3)
with official_left:
    recipient_official_name = st.text_input("Recipient authorized official name")
with official_middle:
    recipient_official_title = st.text_input("Recipient authorized official title")
with official_right:
    recipient_official_email = st.text_input("Recipient authorized official email")

leaving_country = answer_input(
    "Is material, data, equipment, or software leaving the country?",
    "leaving_country",
)
export_controlled = answer_input(
    "Are you shipping export-controlled materials, data, equipment, or software?",
    "export_controlled",
)
reimbursement_cost_or_fee = st.text_input(
    "What reimbursement cost or fee (if any) will UM request from the recipient?"
)
experimental_plan = st.text_area(
    "Recipient's experimental plan for use of the material",
    help="The eRPM worksheet requests a brief description, limited to 200 words.",
)
return_required = answer_input(
    "Is the recipient required to send anything in return for the material?",
    "return_required",
)
previously_invention_report_or_licensed = answer_input(
    "Were these materials previously described in a U-M invention report or licensed by U-M?",
    "previously_invention_report_or_licensed",
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
related_details = st.text_area("Other relevant details about this transfer")
related_documents = st.file_uploader(
    "Related documents (optional)", accept_multiple_files=True
)
sponsor_name = st.text_input("Sponsor name (if applicable)")

st.subheader("Streamlined Eligibility Review")
st.caption(
    "These checklist questions are not all present in eRPM, but they are needed for "
    "the PoC's eligibility result."
)

selected_categories = list(
    dict.fromkeys(MATERIAL_TYPE_TO_CATEGORY[item] for item in material_types)
)
eligibility_answers: dict[str, bool | None] = {}
for criterion in SECTION_CRITERIA["A"]:
    eligibility_answers[criterion.field_id] = tri_state_input(
        criterion.label, criterion.field_id
    )

applicable_sections = [
    section
    for section in ("B", "C", "D", "E")
    if any(CATEGORY_TO_SECTION.get(category) == section for category in selected_categories)
]
if not applicable_sections:
    st.info("Select a material type above to show applicable material questions.")
for section in applicable_sections:
    st.markdown(f"#### {SECTION_TITLES[section]}")
    for criterion in SECTION_CRITERIA[section]:
        eligibility_answers[criterion.field_id] = tri_state_input(
            criterion.label, criterion.field_id
        )

submitted = st.button("Process request", type="primary")

if submitted:
    duration_parts = []
    if duration_years:
        duration_parts.append(f"{duration_years} year(s)")
    if duration_months:
        duration_parts.append(f"{duration_months} month(s)")
    requested_duration = ", ".join(duration_parts)
    if duration_comments.strip():
        requested_duration = " — ".join(
            part for part in (requested_duration, duration_comments.strip()) if part
        )

    erpm_intake = {
        "project_title": project_title,
        "agreement_category": "Material Transfer Agreement",
        "agreement_type": "Outgoing MTA",
        "paying_um_for_material": paying_um_for_material,
        "duration_years": duration_years,
        "duration_months": duration_months,
        "duration_comments": duration_comments,
        "copy_from_existing_ufa": copy_from_existing_ufa,
        "contact_pi_name": contact_pi_name,
        "contact_pi_phone": contact_pi_phone,
        "contact_pi_email": contact_pi_email,
        "primary_research_administrator_name": primary_ra_name,
        "primary_research_administrator_phone": primary_ra_phone,
        "primary_research_administrator_email": primary_ra_email,
        "measurable_personnel_effort": measurable_personnel_effort,
        "material_types": material_types,
        "material_description": material_description,
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
        "external_funding_supported_development": external_funding_supported_development,
        "managed_affiliate_work": managed_affiliate_work,
        "made_using_third_party_materials": made_using_third_party_materials,
        "clinical_health_data_shared": clinical_health_data_shared,
        "related_details": related_details,
        "related_document_names": [document.name for document in related_documents],
        "sponsor_name": sponsor_name,
    }

    request = {
        "erpm_intake": erpm_intake,
        "material_categories": selected_categories,
        "eligibility_answers": eligibility_answers,
        "agreement_information": {
            "recipient_institution_name": recipient_entity,
            "recipient_institution_address": recipient_admin_street_address,
            "recipient_scientist_name": recipient_scientist_name,
            "recipient_scientist_title": recipient_scientist_title,
            "recipient_scientist_email": recipient_scientist_email,
            "recipient_scientist_can_certify_organization": (
                recipient_scientist_can_certify
            ),
            "recipient_authorized_official_name": recipient_official_name,
            "recipient_authorized_official_title": recipient_official_title,
            "recipient_authorized_official_email": recipient_official_email,
            "provider_scientist_name": contact_pi_name,
            "provider_scientist_title": contact_pi_title,
            "provider_scientist_email": contact_pi_email,
            "material_description": material_description,
            "recipient_research_purpose": experimental_plan,
            "requested_duration": requested_duration,
            "shipping_cost_payer": (
                "recipient" if reimbursement_cost_or_fee.strip() else "provider"
            ),
            "material_provided_at_no_cost": (
                None if paying_um_for_material is None else not paying_um_for_material
            ),
            "shipping_recipient_name": shipping_recipient_name,
            "shipping_address": shipping_address,
            "transmittal_fee": reimbursement_cost_or_fee,
        },
    }

    report = build_screening_report(request)
    eligibility = report["eligibility"]

    st.divider()
    st.header("Screening result")
    if eligibility["status"] == "eligible":
        st.success("Eligible for the Streamlined Template Process")
    elif eligibility["status"] == "ineligible":
        st.error("Not eligible for the Streamlined Template Process")
    else:
        st.warning("This request will route to eRPM")
    st.write(eligibility["explanation"])
    st.caption("Evaluated sections: " + ", ".join(eligibility["evaluated_sections"]))

    result_left, result_right = st.columns(2)
    with result_left:
        show_check_list("Passed checks", eligibility["passed_checks"])
        show_check_list("Failed checks", eligibility["failed_checks"])
    with result_right:
        show_check_list(
            "Missing or unresolved information", eligibility["missing_information"]
        )
        readiness = report["agreement_readiness"]
        st.markdown("**Agreement information**")
        st.write(readiness["status"].replace("_", " ").title())
        if readiness["missing_fields"]:
            st.write("Missing: " + ", ".join(readiness["missing_fields"]))

    template_result = report["template_selection"]
    st.markdown("**Automatic template decision**")
    st.write(template_result["status"].replace("_", " ").title())
    if template_result["selected_template"]:
        selected_id = template_result["selected_template"]
        selected_detail = next(
            detail
            for detail in template_result["candidate_details"]
            if detail["template_id"] == selected_id
        )
        st.success("Selected template: " + selected_detail["display_name"])
    if template_result["candidate_templates"]:
        st.write(
            "Document-supported candidates: "
            + ", ".join(template_result["candidate_templates"])
        )
    for reason in template_result["review_reasons"]:
        st.caption(reason)

    pipeline_result = None
    configuration_error = None
    if (
        template_result["status"] == "template_selected"
        and report["agreement_readiness"]["status"] == "ready"
    ):
        try:
            signing_configuration = SigningConfiguration.from_environment()
        except SigningConfigurationError as error:
            configuration_error = str(error)
        else:
            project_root = Path(__file__).resolve().parent
            pipeline = OutgoingMTAPipeline(
                renderer=DocxAgreementRenderer(project_root / "outputs" / "agreements"),
                sender=SignNowPackageSender(
                    project_root / "outputs" / "signing", signing_configuration
                ),
            )
            pipeline_result = pipeline.run(request_id, request)

    st.markdown("**Automation result**")
    if configuration_error:
        st.error("Signing package blocked: " + configuration_error)
    elif pipeline_result is not None:
        if pipeline_result.status == "prepared_for_signature":
            st.success("Agreement and local SignNow package are ready.")
            agreement_path = Path(pipeline_result.artifact_path or "")
            manifest_path = Path(pipeline_result.delivery_reference or "")
            if agreement_path.is_file():
                st.download_button(
                    "Download populated agreement",
                    data=agreement_path.read_bytes(),
                    file_name=agreement_path.name,
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                )
            if manifest_path.is_file():
                st.download_button(
                    "Download signing manifest",
                    data=manifest_path.read_text(encoding="utf-8"),
                    file_name=manifest_path.name,
                    mime="application/json",
                )
        elif pipeline_result.status == "routed_to_erpm":
            st.warning("Request is outside the automatic path and must continue in eRPM.")
        else:
            detail = "; ".join(pipeline_result.reasons) or pipeline_result.status
            st.error("Automatic processing stopped: " + detail)
    elif report["agreement_readiness"]["status"] != "ready":
        st.warning("Complete the missing agreement information and process again.")
    else:
        st.info("No automatic agreement was created; continue this request in eRPM.")

    st.download_button(
        "Download screening report",
        data=serialize_screening_report(report),
        file_name="mta_screening_report.json",
        mime="application/json",
    )
