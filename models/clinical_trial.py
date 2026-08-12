from typing import Optional

from sqlmodel import Field, SQLModel

from settings import settings


class ClinicalTrial(SQLModel, table=True):
    """Normalized record from ClinicalTrials.gov API v2. Doubles as the ORM table row."""

    __tablename__ = settings.clinical_trials_table  # type: ignore[assignment]

    nct_id: str = Field(
        primary_key=True, description="ClinicalTrials.gov identifier, e.g. NCT01234567"
    )
    title: str = Field(description="Brief study title")
    status: str = Field(description="Overall recruitment status, e.g. RECRUITING")
    phase: Optional[str] = Field(default=None, description="Study phase, e.g. PHASE2")
    condition: Optional[str] = Field(default=None, description="Primary condition studied")
    sponsor: Optional[str] = Field(default=None, description="Lead sponsor name")
    summary: Optional[str] = Field(default=None, description="Brief study summary")
    start_date: Optional[str] = Field(default=None, description="Study start date, as reported")
    enrollment_count: Optional[int] = Field(
        default=None, description="Reported/estimated enrollment count"
    )


class Eligibility(SQLModel, table=True):
    """Eligibility criteria for a trial, 1:1 with ClinicalTrial.nct_id (eligibilityModule)."""

    __tablename__ = settings.eligibility_table  # type: ignore[assignment]

    nct_id: str = Field(
        primary_key=True,
        foreign_key=f"{settings.clinical_trials_table}.nct_id",
        description="ClinicalTrials.gov identifier this eligibility record belongs to",
    )
    sex: Optional[str] = Field(default=None, description="Eligible sex, e.g. ALL, MALE, FEMALE")
    minimum_age: Optional[str] = Field(
        default=None, description="Minimum eligible age, as reported, e.g. '18 Years'"
    )
    maximum_age: Optional[str] = Field(
        default=None, description="Maximum eligible age, as reported, e.g. '75 Years'"
    )
    std_ages: Optional[str] = Field(
        default=None, description="Comma-separated standard age groups, e.g. ADULT, OLDER_ADULT"
    )
    healthy_volunteers: Optional[bool] = Field(
        default=None, description="Whether healthy volunteers are accepted"
    )
    population: Optional[str] = Field(
        default=None, description="Description of the study population"
    )
