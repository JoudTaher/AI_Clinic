from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.adapters.docx_renderer import DocxAgreementRenderer
from src.adapters.signnow_package_sender import SignNowPackageSender
from src.materials import (
    HUMAN_MATERIAL_TYPE,
    MATERIAL_TYPES,
    derive_material_categories,
)
from src.pipeline.outgoing_mta import OutgoingMTAPipeline
from src.screening_report import build_screening_report, serialize_screening_report


st.set_page_config(page_title="Outgoing MTA Screening PoC", page_icon="📄", layout="wide")

ANSWER_OPTIONS = ("Not answered", "Yes", "No")
ANSWER_VALUES = {"Not answered": None, "Yes": True, "No": False}

def answer_input(label: str, key: str, help_text: str | None = None) -> bool | None:
    answer = st.selectbox(label, ANSWER_OPTIONS, key=key, help=help_text)
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

st.subheader("Introduction")
st.caption("Agreement Category: Material Transfer Agreement · Agreement Type: Outgoing MTA")
intro_left, intro_right = st.columns(2)
with intro_left:
    project_title = st.text_input("Project Title")
    paying_for_material = answer_input(
        "Are you paying for this material as a product or a service from a company?",
        "paying_for_material_as_product_or_service",
        "This does not include paying a shipping fee.",
    )
with intro_right:
    duration_years = st.number_input(
        "Expected Duration — Years", min_value=0, step=1, value=0
    )
    duration_months = st.number_input(
        "Expected Duration — Months", min_value=0, step=1, value=0
    )
    duration_comments = st.text_area("Duration Comments")

st.subheader("Personnel")
personnel_left, personnel_right = st.columns(2)
with personnel_left:
    contact_pi_name = st.text_input("Contact PI")
with personnel_right:
    primary_ra_name = st.text_input("Primary Research Administrator")
measurable_personnel_effort = answer_input(
    "Is there measurable personnel effort for the project that is related to the unfunded agreement?",
    "measurable_personnel_effort",
)

st.subheader("Material Details")
material_types = st.multiselect("Material Type", options=MATERIAL_TYPES)
human_derived_description = ""
human_data_classification = ""
irb_study_number = ""
protocol_consent_transfer_sections = ""
if HUMAN_MATERIAL_TYPE in material_types:
    human_derived_description = st.text_area(
        "Human derived tissue/samples description"
    )
    human_data_classification = st.text_area("How are these materials classified?")
    irb_study_number = st.text_input("IRB study HUM number")
    protocol_consent_transfer_sections = st.text_area(
        "Protocol and informed-consent sections allowing transfer outside U-M"
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
project_administrative_home = st.text_input("Project Administrative Home")
will_deposit_in_repository = answer_input(
    "Will the material be deposited in a repository?", "will_deposit_in_repository"
)

recipient_left, recipient_right = st.columns(2)
with recipient_left:
    recipient_entity = st.text_input("Recipient Entity")
    recipient_scientist_name = st.text_input("Recipient Scientist Name")
    recipient_scientist_email = st.text_input("Recipient Scientist Email")
with recipient_right:
    recipient_admin_name = st.text_input("Recipient Administrative Contact Name")
    recipient_admin_email = st.text_input("Recipient Administrative Contact Email")
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
reimbursement_cost_or_fee = st.text_input(
    "What reimbursement cost or fee, if any, will U-M request from the recipient?"
)
experimental_plan = st.text_area(
    "Recipient's experimental plan for use of the material",
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
    innovation_partnerships_file_number = st.text_input(
        "Innovation Partnerships File Number"
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
supported_categories = {"chemical", "animal_derived", "biological", "device"}

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
if selected_category in supported_categories:
    name_left, name_right = st.columns(2)
    with name_left:
        st.caption(
            f"Provider Scientist full name: {contact_pi_name or 'Not entered above'}"
        )
    with name_right:
        st.caption(
            "Recipient Scientist full name: "
            f"{recipient_scientist_name or 'Not entered above'}"
        )

    agreement_left, agreement_right = st.columns(2)
    with agreement_left:
        provider_scientist_title = st.text_input(
            "Provider Scientist academic/job title (if known)"
        )
        provider_scientist_email = st.text_input(
            "Provider Scientist signing email",
            help="Used to deliver the signing request; it is not printed in the agreement.",
        )
        if selected_category in {"chemical", "animal_derived", "biological"}:
            recipient_scientist_title = st.text_input(
                "Recipient Scientist academic/job title (if known)"
            )
    with agreement_right:
        recipient_institution_address = st.text_area("Recipient Organization address")
        material_label = (
            "Original Material description"
            if selected_category == "biological"
            else "Material description"
        )
        material_description = st.text_area(material_label)

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

    if selected_category in {"chemical", "animal_derived"}:
        shipping_left, shipping_right = st.columns(2)
        with shipping_left:
            shipping_recipient_name = st.text_input("Shipping recipient name")
        with shipping_right:
            shipping_address = st.text_area("Shipping address")

    if selected_category == "biological":
        recipient_scientist_can_certify = answer_input(
            "Recipient Scientist authorized to certify for Recipient Organization?",
            "recipient_scientist_can_certify_organization",
        )

    requires_recipient_official = selected_category in {
        "chemical",
        "animal_derived",
        "device",
    } or (
        selected_category == "biological"
        and recipient_scientist_can_certify is False
    )
    if requires_recipient_official:
        official_role = (
            "Recipient Authorized Signatory"
            if selected_category in {"chemical", "animal_derived"}
            else "Recipient Authorized Official"
        )
        official_left, official_middle, official_right = st.columns(3)
        with official_left:
            recipient_official_name = st.text_input(f"{official_role} name")
        with official_middle:
            recipient_official_title = st.text_input(f"{official_role} title")
        with official_right:
            recipient_official_email = st.text_input(
                f"{official_role} signing email",
                help="Used to deliver the signing request; it is not printed in the agreement.",
            )
else:
    st.info(
        "Select exactly one supported material category to show the matching agreement fields."
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
    if selected_category in supported_categories:
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
    if selected_category in {"chemical", "animal_derived", "biological"}:
        agreement_information["recipient_scientist_title"] = recipient_scientist_title
    if selected_category in {"chemical", "animal_derived"}:
        agreement_information.update(
            {
                "shipping_recipient_name": shipping_recipient_name,
                "shipping_address": shipping_address,
            }
        )
    if selected_category == "biological":
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

    project_root = Path(__file__).resolve().parent
    pipeline = OutgoingMTAPipeline(
        renderer=DocxAgreementRenderer(project_root / "outputs" / "agreements"),
        sender=SignNowPackageSender(project_root / "outputs" / "signing"),
    )
    pipeline_result = pipeline.run(request)

    st.markdown("**Automation result**")
    if pipeline_result.status == "prepared_for_signature":
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
        if manifest_path.is_file():
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
