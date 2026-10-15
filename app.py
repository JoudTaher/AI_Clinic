from __future__ import annotations

import streamlit as st

from src.eligibility import CATEGORY_TO_SECTION, SECTION_CRITERIA
from src.screening_report import build_screening_report, serialize_screening_report


st.set_page_config(page_title="Outgoing MTA Screening PoC", page_icon="📄", layout="wide")

ANSWER_OPTIONS = ("Unknown", "Yes", "No")
ANSWER_VALUES = {"Unknown": None, "Yes": True, "No": False}

CATEGORY_LABELS = {
    "Chemical": "chemical",
    "Biological": "biological",
    "Device": "device",
    "Animal derived": "animal_derived",
    "Other or uncertain": "other",
}

SECTION_TITLES = {
    "A": "Section A General eligibility",
    "B": "Section B Chemical materials",
    "C": "Section C Biological materials",
    "D": "Section D Devices",
    "E": "Section E Animal materials",
}


def tri_state_input(label: str, field_id: str) -> bool | None:
    answer = st.selectbox(
        label,
        ANSWER_OPTIONS,
        key=f"eligibility_{field_id}",
        help="Choose Yes only when the checklist statement is confirmed true.",
    )
    return ANSWER_VALUES[answer]


def show_check_list(title: str, items: list[dict]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption("None")
        return
    for item in items:
        st.markdown(f"- {item['label']}  \n  `[{item['field_id']}]`")


st.title("Outgoing MTA Screening Proof of Concept")
st.caption(
    "Local demonstration only · Not connected to eRPM · Not legal approval · Use synthetic data"
)
st.write(
    "Complete the checklist below to test whether a request meets the supplied "
    "criteria for the Streamlined Template Process."
)

selected_labels = st.multiselect(
    "Material categories",
    options=list(CATEGORY_LABELS),
    help="Select every category that applies. Multiple categories are supported.",
)
selected_categories = [CATEGORY_LABELS[label] for label in selected_labels]

with st.form("mta_intake"):
    st.subheader("Part A General eligibility")
    eligibility_answers: dict[str, bool | None] = {}
    for criterion in SECTION_CRITERIA["A"]:
        eligibility_answers[criterion.field_id] = tri_state_input(
            criterion.label, criterion.field_id
        )

    st.subheader("Part B Material specific eligibility")
    applicable_sections = [
        section
        for section in ("B", "C", "D", "E")
        if any(
            CATEGORY_TO_SECTION.get(category) == section
            for category in selected_categories
        )
    ]
    if not applicable_sections:
        st.info("Select one or more material categories above to show applicable questions.")
    for section in applicable_sections:
        st.markdown(f"#### {SECTION_TITLES[section]}")
        for criterion in SECTION_CRITERIA[section]:
            eligibility_answers[criterion.field_id] = tri_state_input(
                criterion.label, criterion.field_id
            )

    st.subheader("Part C Agreement information")
    left, right = st.columns(2)
    with left:
        recipient_institution_name = st.text_input("Recipient institution")
        recipient_institution_address = st.text_area("Recipient institution address")
        recipient_scientist_name = st.text_input("Recipient scientist")
        provider_scientist_name = st.text_input("Provider scientist")
        material_description = st.text_area("Material information")
    with right:
        recipient_research_purpose = st.text_area("Recipient research purpose")
        requested_duration = st.text_input(
            "Requested duration", placeholder="For example 3 years"
        )
        shipping_cost_label = st.selectbox(
            "Who will pay shipping costs?",
            ("Unknown", "Recipient", "Provider", "Other"),
        )
        no_cost_label = st.selectbox(
            "Will the provider scientist provide the material at no cost?",
            ANSWER_OPTIONS,
        )

    with st.expander("Optional template information"):
        recipient_scientist_title = st.text_input("Recipient scientist title")
        provider_scientist_title = st.text_input("Provider scientist title")
        shipping_name = st.text_input("Shipping contact name")
        shipping_address = st.text_area("Shipping address")
        transmittal_fee_amount = st.text_input("Transmittal fee amount")
        um_reference_number = st.text_input("UM reference number")
        um_technology_transfer_file_number = st.text_input(
            "UM technology transfer file number"
        )

    submitted = st.form_submit_button("Screen request", type="primary")

if submitted:
    shipping_cost_payer = {
        "Unknown": None,
        "Recipient": "recipient",
        "Provider": "provider",
        "Other": "other",
    }[shipping_cost_label]

    request = {
        "material_categories": selected_categories,
        "eligibility_answers": eligibility_answers,
        "agreement_information": {
            "recipient_institution_name": recipient_institution_name,
            "recipient_institution_address": recipient_institution_address,
            "recipient_scientist_name": recipient_scientist_name,
            "recipient_scientist_title": recipient_scientist_title,
            "provider_scientist_name": provider_scientist_name,
            "provider_scientist_title": provider_scientist_title,
            "material_description": material_description,
            "recipient_research_purpose": recipient_research_purpose,
            "requested_duration": requested_duration,
            "shipping_cost_payer": shipping_cost_payer,
            "material_provided_at_no_cost": ANSWER_VALUES[no_cost_label],
            "shipping_name": shipping_name,
            "shipping_address": shipping_address,
            "transmittal_fee_amount": transmittal_fee_amount,
            "um_reference_number": um_reference_number,
            "um_technology_transfer_file_number": um_technology_transfer_file_number,
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
        st.warning("Manual review required")
    st.write(eligibility["explanation"])
    st.caption("Evaluated sections: " + ", ".join(eligibility["evaluated_sections"]))

    result_left, result_right = st.columns(2)
    with result_left:
        show_check_list("Passed checks", eligibility["passed_checks"])
        show_check_list("Failed checks", eligibility["failed_checks"])
    with result_right:
        show_check_list("Missing or unresolved information", eligibility["missing_information"])
        readiness = report["agreement_readiness"]
        st.markdown("**Agreement information**")
        st.write(readiness["status"].replace("_", " ").title())
        if readiness["missing_fields"]:
            st.write("Missing: " + ", ".join(readiness["missing_fields"]))

    template_result = report["template_selection"]
    st.markdown("**Template review**")
    st.write(template_result["status"].replace("_", " ").title())
    if template_result["candidate_templates"]:
        st.write(
            "Document-supported candidates: "
            + ", ".join(template_result["candidate_templates"])
        )
    for reason in template_result["review_reasons"]:
        st.caption(reason)

    st.download_button(
        "Download screening report",
        data=serialize_screening_report(report),
        file_name="mta_screening_report.json",
        mime="application/json",
    )

