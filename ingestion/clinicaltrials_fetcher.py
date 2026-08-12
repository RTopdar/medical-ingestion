"""Fetch dummy clinical trial records from ClinicalTrials.gov API v2."""

import time

import requests

from models.clinical_trial import ClinicalTrial, Eligibility

CTGOV_API = "https://clinicaltrials.gov/api/v2"


def search_trials(condition: str, max_results: int = 20) -> list[dict]:
    """
    Search ClinicalTrials.gov for studies matching a condition.

    Args:
        condition: Condition/disease search term, e.g. "diabetes"
        max_results: Max studies to return (API page size)

    Returns:
        List of raw study dicts (protocolSection)
    """
    resp = requests.get(
        f"{CTGOV_API}/studies",
        params={"query.cond": condition, "pageSize": max_results},
    )
    resp.raise_for_status()

    return [study["protocolSection"] for study in resp.json().get("studies", [])]


def parse_trial(study: dict) -> ClinicalTrial:
    """
    Convert a raw protocolSection dict into a ClinicalTrial model.

    Args:
        study: protocolSection dict from the ClinicalTrials.gov API

    Returns:
        ClinicalTrial
    """
    identification = study.get("identificationModule", {})
    status = study.get("statusModule", {})
    conditions = study.get("conditionsModule", {})
    design = study.get("designModule", {})
    sponsor = study.get("sponsorCollaboratorsModule", {})
    description = study.get("descriptionModule", {})

    phases = design.get("phases") or []

    return ClinicalTrial(
        nct_id=identification["nctId"],
        title=identification.get("briefTitle", "Unknown"),
        status=status.get("overallStatus", "UNKNOWN"),
        phase=phases[0] if phases else None,
        condition=", ".join(conditions.get("conditions", [])) or None,
        sponsor=sponsor.get("leadSponsor", {}).get("name"),
        summary=description.get("briefSummary"),
        start_date=status.get("startDateStruct", {}).get("date"),
        enrollment_count=design.get("enrollmentInfo", {}).get("count"),
    )


def parse_eligibility(study: dict) -> Eligibility:
    """
    Convert a raw protocolSection dict into an Eligibility model.

    Args:
        study: protocolSection dict from the ClinicalTrials.gov API

    Returns:
        Eligibility
    """
    identification = study.get("identificationModule", {})
    eligibility = study.get("eligibilityModule", {})

    std_ages = eligibility.get("stdAges") or []

    return Eligibility(
        nct_id=identification["nctId"],
        sex=eligibility.get("sex"),
        minimum_age=eligibility.get("minimumAge"),
        maximum_age=eligibility.get("maximumAge"),
        std_ages=", ".join(std_ages) or None,
        healthy_volunteers=eligibility.get("healthyVolunteers"),
        population=eligibility.get("studyPopulation") or None,
    )


def fetch_dummy_trials(
    condition: str = "diabetes", count: int = 20
) -> tuple[list[ClinicalTrial], list[Eligibility]]:
    """
    Fetch and parse dummy trial + eligibility records for a condition.

    Args:
        condition: Condition/disease search term
        count: Number of trials to fetch

    Returns:
        Tuple of (ClinicalTrial models, Eligibility models), each 1:1 by nct_id
    """
    print(f"Searching ClinicalTrials.gov for: {condition}")
    studies = search_trials(condition, max_results=count)

    trials, eligibility_records = [], []
    for study in studies:
        try:
            trials.append(parse_trial(study))
            eligibility_records.append(parse_eligibility(study))
        except Exception as e:
            nct_id = study.get("identificationModule", {}).get("nctId", "unknown")
            print(f"  Error parsing {nct_id}: {e}")
        time.sleep(0.1)  # Rate limit courtesy

    print(f"  Parsed {len(trials)}/{len(studies)} trials")
    return trials, eligibility_records


if __name__ == "__main__":
    import sys

    condition = sys.argv[1] if len(sys.argv) > 1 else "diabetes"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    trials, eligibility_records = fetch_dummy_trials(condition, count=count)
    for trial, elig in zip(trials[:5], eligibility_records[:5]):
        print(
            f"  {trial.nct_id}: {trial.title} [{trial.status}] eligibility={elig.sex} {elig.minimum_age}-{elig.maximum_age}"
        )
