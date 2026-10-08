"""
Demo data seed script.

Creates one realistic organization/project so the API and frontend have
something to show without a person having to click it all together by
hand. Every record goes through the same services/selectors the API
itself uses (apps.accounts, apps.organizations.services,
apps.projects.services, apps.projects.selectors, apps.variations.services,
apps.risks.services, apps.inspections.services, apps.documents.services)
— nothing here writes directly to a model that has a service, so the
seeded data obeys the same validation, status-transition, and file-upload
rules real requests do. Evidence and document "files" are small in-memory
byte strings built to actually pass the real magic-byte signature check
in common.file_validation — not placeholders that bypass it.

Idempotent: safe to run more than once. If the demo organization already
has the demo project, the script prints a message and exits without
creating duplicates or re-running the payment/variation/risk/issue/
inspection/document workflows.

Creates:
    - User:          demo@glintpm.dev (password: DemoPass123!)
    - Organization:  "GlintPM Private Demo", with that user as
                      ORGANIZATION_ADMIN
    - Project:       "Luxury Residence — Lekki" (LRL-001, NGN
                      500,000,000, ESTATE_DEVELOPMENT, ACTIVE)
    - ProjectBudget with 7 BudgetItems across the standard categories
    - 4 ProgressUpdates (historical, monthly, actual trailing plan)
    - 5 PaymentApplications, one per point in the review lifecycle:
      SUBMITTED, UNDER_REVIEW, RECOMMENDED, REJECTED, and one carried
      all the way through to PARTIALLY_PAID.
    - 4 Variations, one per point in the review lifecycle: PROPOSED,
      UNDER_REVIEW, APPROVED (via the dedicated /approve/ flow), and
      REJECTED — so the dashboard's approved_variations_total and
      pending_variations_exposure both have real, distinguishable data.
    - 5 Risks spanning categories, responses, and every RiskStatus
      (OPEN, MITIGATING, MONITORING, CLOSED), scored via probability x
      impact so the risk register shows a realistic spread from LOW to
      HIGH.
    - 4 Issues spanning every severity and every IssueStatus (OPEN,
      IN_PROGRESS, RESOLVED, CLOSED), with resolution text recorded on
      the ones that reached RESOLVED/CLOSED.
    - 3 Inspections spanning the workflow: one COMPLETED with an
      OBSERVATION overall result, one COMPLETED with a FAIL overall
      result (payment verification — a real defect found), and one still
      IN_PROGRESS with no items yet.
    - 4 ProjectEvidence files (two linked to inspections, two standalone —
      a progress video and a signed delivery note), each a real small
      JPEG/MP4/PDF that passes magic-byte validation, never a fake stub.
    - 3 DocumentFolders ("Contracts", "Drawings", and "Signed Copies"
      nested under "Contracts") and 3 Documents: a CONTRACT (carried to
      version 2, demonstrating versioning), a DRAWING, and a BOQ with no
      folder.

Run with:
    python manage.py shell -c "import scripts.seed_demo_data as s; s.run()"
"""

from datetime import date, datetime
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import User
from apps.documents import services as document_services
from apps.inspections import services as inspection_services
from apps.organizations import services as org_services
from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.projects import services as project_services
from apps.projects.models import Project, ProjectType
from apps.risks import services as risk_services
from apps.variations import services as variation_services

DEMO_USER_EMAIL = "demo@glintpm.dev"
DEMO_USER_PASSWORD = "DemoPass123!"

ORGANIZATION_NAME = "GlintPM Private Demo"
PROJECT_CODE = "LRL-001"

# (category, code, description, original, approved, committed, actual)
BUDGET_ITEMS = [
    (
        "CIVIL",
        "C-01",
        "Substructure & foundations",
        "60000000.00",
        "62000000.00",
        "58000000.00",
        "55000000.00",
    ),
    (
        "STRUCTURAL",
        "S-01",
        "Superstructure frame",
        "95000000.00",
        "98000000.00",
        "90000000.00",
        "78000000.00",
    ),
    (
        "ARCHITECTURAL",
        "A-01",
        "Envelope & roofing",
        "45000000.00",
        "45000000.00",
        "40000000.00",
        "22000000.00",
    ),
    (
        "MEP",
        "M-01",
        "Mechanical, electrical & plumbing",
        "70000000.00",
        "73000000.00",
        "65000000.00",
        "31000000.00",
    ),
    (
        "FINISHES",
        "F-01",
        "Interior finishes & fittings",
        "80000000.00",
        "85000000.00",
        "40000000.00",
        "9000000.50",
    ),
    (
        "EXTERNAL_WORKS",
        "E-01",
        "Landscaping & external works",
        "18000000.00",
        "18000000.00",
        "5000000.00",
        "0.00",
    ),
    (
        "PROFESSIONAL_FEES",
        "P-01",
        "Design, PM & consultancy fees",
        "22000000.00",
        "24000000.00",
        "22000000.00",
        "15000000.00",
    ),
]

# (reporting_date, planned_percent, actual_percent, notes)
PROGRESS_UPDATES = [
    (
        date(2026, 6, 30),
        "20.00",
        "18.00",
        "Foundation works underway; minor delay clearing site access.",
    ),
    (
        date(2026, 7, 31),
        "38.00",
        "33.00",
        "Substructure complete. Rebar shortage slowed frame start.",
    ),
    (
        date(2026, 8, 31),
        "58.00",
        "49.50",
        "Superstructure frame to 3rd floor. Rain days affected concrete pours.",
    ),
    (
        date(2026, 9, 15),
        "66.00",
        "55.50",
        "Roofing 60% complete; MEP first-fix started on lower floors.",
    ),
]

# (variation_number, title, description, reason, category, requested,
#  estimated, target_lifecycle_status)
# target_lifecycle_status drives _seed_variations below: how far through
# PROPOSED -> UNDER_REVIEW -> APPROVED / REJECTED each sample is taken.
VARIATIONS = [
    (
        "VO-001",
        "Additional soakaway pit",
        "Existing soakaway undersized for revised drainage design.",
        "Site survey found groundwater table higher than geotechnical report indicated.",
        "SITE_CONDITION",
        "8500000.00",
        "7200000.00",
        "PROPOSED",
    ),
    (
        "VO-002",
        "Upgrade sanitaryware specification",
        "Client requested higher-end sanitaryware brand across all bathrooms.",
        "Client site visit; revised finishes brief issued.",
        "CLIENT_REQUEST",
        "6000000.00",
        "5500000.00",
        "UNDER_REVIEW",
    ),
    (
        "VO-003",
        "Structural steel redesign for pool house",
        "Pool house roof structure redesigned to clear-span steel trusses.",
        "Architect's revised design to open up pool house sightlines.",
        "DESIGN_CHANGE",
        "22000000.00",
        "20000000.00",
        "APPROVED",
    ),
    (
        "VO-004",
        "Imported marble upgrade",
        "Client requested imported marble in place of specified local granite.",
        "Client preference change after showroom visit.",
        "CLIENT_REQUEST",
        "30000000.00",
        "28000000.00",
        "REJECTED",
    ),
]

# (title, description, category, probability, impact, response, mitigation,
#  contingency, target_date, target_lifecycle_status)
RISKS = [
    (
        "Rainy season delays substructure works",
        "Peak rainy season overlaps with excavation and foundation pours.",
        "SCHEDULE",
        4,
        4,
        "MITIGATE",
        "Sequence pours around forecast dry windows; hire additional dewatering pumps.",
        "Add 3-week schedule buffer before superstructure milestone.",
        date(2026, 10, 31),
        "MITIGATING",
    ),
    (
        "Cement price volatility",
        "Local cement prices have risen 12% in the last quarter.",
        "COST",
        3,
        4,
        "ACCEPT",
        "",
        "Contingency line held in professional fees budget category.",
        None,
        "OPEN",
    ),
    (
        "Sole-sourced marble supplier delay",
        "Only one supplier can meet the imported marble specification.",
        "PROCUREMENT",
        2,
        5,
        "TRANSFER",
        "Back-to-back supply contract with liquidated damages clause.",
        "Identify a secondary supplier as fallback if lead time slips.",
        date(2026, 11, 30),
        "MONITORING",
    ),
    (
        "Site security breach risk",
        "Perimeter fencing incomplete on the eastern boundary.",
        "SAFETY",
        2,
        3,
        "MITIGATE",
        "Temporary hoarding and night security until permanent fence complete.",
        "",
        date(2026, 7, 31),
        "OPEN",
    ),
    (
        "Regulatory approval delay for pool house",
        "Pool house is an addition to the originally approved building plan.",
        "REGULATORY",
        1,
        3,
        "ACCEPT",
        "Submitted amended plan approval application early.",
        "",
        date(2026, 8, 15),
        "CLOSED",
    ),
]

# (title, description, severity, target_date, target_lifecycle_status,
#  resolution)
ISSUES = [
    (
        "Cracked slab found on level 2",
        "Hairline cracks visible on level 2 slab near the northeast column.",
        "HIGH",
        date(2026, 10, 1),
        "IN_PROGRESS",
        "",
    ),
    (
        "Water ingress in basement parking",
        "Standing water observed in basement parking after heavy rain.",
        "CRITICAL",
        date(2026, 9, 30),
        "OPEN",
        "",
    ),
    (
        "Incorrect tile batch delivered",
        "Delivered floor tile batch does not match the approved sample.",
        "MEDIUM",
        date(2026, 8, 1),
        "RESOLVED",
        "Supplier collected incorrect batch and redelivered the correct one on 2026-08-05.",
    ),
    (
        "Generator noise complaint from neighbor",
        "Adjacent property raised a noise complaint about the site generator.",
        "LOW",
        date(2026, 7, 1),
        "CLOSED",
        "Generator relocated and acoustic enclosure installed; complainant confirmed resolved.",
    ),
]

# Minimal but genuinely valid file content for each kind — real magic
# bytes, so apps.inspections/documents.services' upload validation (see
# common.file_validation) is exercised for real, not bypassed.
_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 100
_MP4_BYTES = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100
_PDF_BYTES = b"%PDF-1.4\n%demo content\n%%EOF"


def _jpeg(name: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, _JPEG_BYTES, content_type="image/jpeg")


def _mp4(name: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, _MP4_BYTES, content_type="video/mp4")


def _pdf(name: str, extra: bytes = b"") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, _PDF_BYTES + extra, content_type="application/pdf")


# (inspection_type, inspection_date, location, summary, recommendations,
#  items, target_lifecycle_status)
# items: list of (category, description, item_status, severity, recommendation)
INSPECTIONS = [
    (
        "ROUTINE",
        date(2026, 7, 15),
        "Whole site",
        "Monthly routine walk-through of the Lekki residence site.",
        "Continue current housekeeping standard.",
        [
            ("SAFETY", "Site hoarding and signage intact", "PASS", "LOW", ""),
            ("PROGRESS", "Works proceeding per programme", "PASS", "LOW", ""),
            (
                "DOCUMENTATION",
                "Daily site diary missing entries for two days",
                "OBSERVATION",
                "LOW",
                "Remind site team to complete the diary daily.",
            ),
        ],
        "COMPLETED",
    ),
    (
        "PAYMENT_VERIFICATION",
        date(2026, 9, 10),
        "Level 2",
        "Verification inspection supporting payment application PA-0002.",
        "Withhold sign-off on affected bathrooms pending re-grouting.",
        [
            ("QUALITY", "Tile grouting uneven in level 2 bathrooms", "FAIL", "MEDIUM", "Re-grout affected area before payment certification."),
            ("PROGRESS", "Claimed quantities match site measurement", "PASS", "LOW", ""),
        ],
        "COMPLETED",
    ),
    (
        "QUALITY",
        date(2026, 9, 20),
        "Pool house",
        "In-progress quality check on the pool house steel structure.",
        "",
        [],
        "IN_PROGRESS",
    ),
]

# (title, description, evidence_type, file_builder, captured_at, inspection_index_or_None)
# inspection_index_or_None indexes into INSPECTIONS above (0-based), or
# None for standalone evidence not tied to any inspection.
EVIDENCE = [
    (
        "Site hoarding and signage",
        "Photo confirming perimeter hoarding and safety signage in place.",
        "PHOTO",
        lambda: _jpeg("hoarding.jpg"),
        datetime(2026, 7, 15, 9, 30, tzinfo=dt_timezone.utc),
        0,
    ),
    (
        "Uneven tile grouting — level 2 bathroom",
        "Close-up of the grouting defect referenced in the payment verification inspection.",
        "PHOTO",
        lambda: _jpeg("grouting-defect.jpg"),
        datetime(2026, 9, 10, 11, 15, tzinfo=dt_timezone.utc),
        1,
    ),
    (
        "September progress walkthrough",
        "Standalone video walkthrough of the site, not tied to a specific inspection.",
        "VIDEO",
        lambda: _mp4("progress-walkthrough.mp4"),
        datetime(2026, 9, 15, 14, 0, tzinfo=dt_timezone.utc),
        None,
    ),
    (
        "Signed material delivery note",
        "Scanned, signed delivery note for the structural steel delivery.",
        "DOCUMENT",
        lambda: _pdf("delivery-note.pdf"),
        None,
        None,
    ),
]

# (name, description, parent_name_or_None)
FOLDERS = [
    ("Contracts", "Executed contracts and agreements.", None),
    ("Drawings", "Architectural and structural drawings.", None),
    ("Signed Copies", "Fully executed, signed contract copies.", "Contracts"),
]

# (name, document_type, folder_name_or_None, file_builder, versions)
# versions: list of change_notes for each version after the first (so
# len(versions) additional POSTs to /versions/ happen after creation).
DOCUMENTS = [
    (
        "Main Building Contract",
        "CONTRACT",
        "Signed Copies",
        lambda: _pdf("main-contract-v1.pdf"),
        ["Updated clause 5.2 on variation valuation after legal review."],
    ),
    (
        "Ground Floor Plan",
        "DRAWING",
        "Drawings",
        lambda: _jpeg("ground-floor-plan.jpg"),
        [],
    ),
    (
        "Bill of Quantities",
        "BOQ",
        None,
        lambda: _pdf("boq.pdf"),
        [],
    ),
]


def _get_or_create_demo_user() -> User:
    user, created = User.objects.get_or_create(
        email=DEMO_USER_EMAIL,
        defaults={"first_name": "Demo", "last_name": "Owner"},
    )
    if created:
        user.set_password(DEMO_USER_PASSWORD)
        user.save(update_fields=["password"])
        print(f"Created user {user.email}")
    else:
        print(f"User {user.email} already exists")
    return user


def _get_or_create_demo_organization(owner: User) -> Organization:
    organization = Organization.objects.filter(name=ORGANIZATION_NAME).first()
    if organization is not None:
        print(f"Organization '{organization.name}' already exists")
        return organization

    organization = org_services.create_organization(
        creator=owner, name=ORGANIZATION_NAME
    )
    print(f"Created organization '{organization.name}' ({organization.slug})")
    return organization


def _ensure_membership(user: User, organization: Organization) -> None:
    _, created = OrganizationMembership.objects.get_or_create(
        user=user,
        organization=organization,
        defaults={"role": Role.ORGANIZATION_ADMIN},
    )
    if created:
        print(f"Added {user.email} to '{organization.name}' as {Role.ORGANIZATION_ADMIN}")


def _create_project(organization: Organization) -> Project:
    project = project_services.create_project(
        organization=organization,
        name="Luxury Residence — Lekki",
        project_code=PROJECT_CODE,
        description=(
            "Five-bedroom luxury residence with staff quarters, pool house "
            "and basement parking."
        ),
        location="Lekki, Lagos",
        client_name="Adeyemi Family Trust",
        contractor_name="Marbleworks Construction Ltd",
        project_type=ProjectType.ESTATE_DEVELOPMENT,
        contract_value=Decimal("500000000.00"),
        currency="NGN",
        planned_start_date=date(2026, 6, 1),
        planned_end_date=date(2027, 8, 31),
        actual_start_date=date(2026, 6, 8),
    )
    print(f"Created project {project.project_code} — {project.name}")
    return project


def _add_budget_items(project: Project) -> None:
    for (
        category,
        code,
        description,
        original,
        approved,
        committed,
        actual,
    ) in BUDGET_ITEMS:
        project_services.add_budget_item(
            project=project,
            category=category,
            code=code,
            description=description,
            original_amount=Decimal(original),
            approved_amount=Decimal(approved),
            committed_amount=Decimal(committed),
            actual_amount=Decimal(actual),
        )
    print(f"Added {len(BUDGET_ITEMS)} budget items")


def _add_progress_updates(project: Project, submitted_by: User) -> None:
    for reporting_date, planned, actual, notes in PROGRESS_UPDATES:
        project_services.add_progress_update(
            project=project,
            submitted_by=submitted_by,
            reporting_date=reporting_date,
            planned_progress_percent=Decimal(planned),
            actual_progress_percent=Decimal(actual),
            notes=notes,
        )
    print(f"Added {len(PROGRESS_UPDATES)} progress updates")


def _seed_payments(project: Project, submitter: User, reviewer: User) -> None:
    """
    One payment application per point in the review lifecycle, so the
    Payments page and dashboard have a realistic mix to render.
    """
    # 1. PA-0001: submitted, untouched — shows up as pending.
    project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("35000000.00"),
        submission_date=date(2026, 7, 15),
    )

    # 2. PA-0002: moved into review — also pending.
    payment = project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("42000000.00"),
        submission_date=date(2026, 8, 5),
    )
    project_services.PaymentService.review(
        payment=payment, reviewer=reviewer, decision="START_REVIEW"
    )

    # 3. PA-0003: recommended for a lower amount than requested — pending.
    payment = project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("60000000.00"),
        submission_date=date(2026, 8, 20),
    )
    project_services.PaymentService.review(
        payment=payment, reviewer=reviewer, decision="START_REVIEW"
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="RECOMMEND",
        amount=Decimal("54000000.00"),
        notes="Deducted unapproved variation on tiling spec.",
    )

    # 4. PA-0004: rejected — a duplicate of an already-paid claim.
    payment = project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("15000000.00"),
        submission_date=date(2026, 6, 25),
    )
    project_services.PaymentService.review(
        payment=payment, reviewer=reviewer, decision="START_REVIEW"
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="REJECT",
        notes="Duplicate of items already covered under PA-0000 (pre-seed).",
    )

    # 5. PA-0005: taken all the way to a partial payment — approved
    #    28,000,000 recommended in full, but only 18,000,000 paid so far.
    payment = project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("28000000.00"),
        submission_date=date(2026, 6, 10),
    )
    project_services.PaymentService.review(
        payment=payment, reviewer=reviewer, decision="START_REVIEW"
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="RECOMMEND",
        amount=Decimal("28000000.00"),
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="APPROVE",
        amount=Decimal("28000000.00"),
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="RECORD_PAYMENT",
        amount=Decimal("18000000.00"),
    )

    print("Seeded 5 payment applications across the full review lifecycle")


def _seed_variations(project: Project, created_by: User, approver: User) -> None:
    """
    One variation per point in its review lifecycle, so the dashboard's
    approved_variations_total (VO-003 only) and pending_variations_exposure
    (VO-001 + VO-002) are both non-zero and clearly distinguishable, and
    REJECTED (VO-004) demonstrably contributes to neither.
    """
    for (
        variation_number,
        title,
        description,
        reason,
        category,
        requested_amount,
        estimated_amount,
        target_status,
    ) in VARIATIONS:
        variation = variation_services.create_variation(
            project=project,
            created_by=created_by,
            variation_number=variation_number,
            title=title,
            description=description,
            reason=reason,
            category=category,
            requested_amount=Decimal(requested_amount),
            estimated_amount=Decimal(estimated_amount),
        )

        if target_status == "PROPOSED":
            continue

        if target_status == "UNDER_REVIEW":
            variation_services.update_variation(
                variation=variation, data={"status": "UNDER_REVIEW"}
            )
        elif target_status == "APPROVED":
            variation_services.update_variation(
                variation=variation, data={"status": "UNDER_REVIEW"}
            )
            variation_services.approve_variation(
                variation=variation,
                approver=approver,
                approved_amount=Decimal(estimated_amount) - Decimal("500000.00"),
                notes="Approved after QS review; scope confirmed against site instruction.",
            )
        elif target_status == "REJECTED":
            variation_services.update_variation(
                variation=variation, data={"status": "REJECTED"}
            )

    print(f"Seeded {len(VARIATIONS)} variations across PROPOSED/UNDER_REVIEW/APPROVED/REJECTED")


def _seed_risks(project: Project, owner: User) -> None:
    for (
        title,
        description,
        category,
        probability,
        impact,
        response,
        mitigation,
        contingency,
        target_date,
        target_status,
    ) in RISKS:
        risk = risk_services.create_risk(
            project=project,
            owner=owner,
            title=title,
            description=description,
            category=category,
            probability=probability,
            impact=impact,
            response=response,
            mitigation=mitigation,
            contingency=contingency,
            target_date=target_date,
        )

        if target_status != "OPEN":
            risk_services.update_risk(risk=risk, data={"status": target_status})

    print(f"Seeded {len(RISKS)} risks spanning OPEN/MITIGATING/MONITORING/CLOSED")


def _seed_issues(project: Project, owner: User) -> None:
    for (
        title,
        description,
        severity,
        target_date,
        target_status,
        resolution,
    ) in ISSUES:
        issue = risk_services.create_issue(
            project=project,
            owner=owner,
            title=title,
            description=description,
            severity=severity,
            target_date=target_date,
        )

        if target_status == "OPEN":
            continue

        data = {"status": target_status}
        if resolution:
            data["resolution"] = resolution
        risk_services.update_issue(issue=issue, data=data)

    print(f"Seeded {len(ISSUES)} issues spanning OPEN/IN_PROGRESS/RESOLVED/CLOSED")


def _seed_inspections_and_evidence(project: Project, inspector: User) -> None:
    inspections = []
    for (
        inspection_type,
        inspection_date,
        location,
        summary,
        recommendations,
        items,
        target_status,
    ) in INSPECTIONS:
        inspection = inspection_services.create_inspection(
            project=project,
            inspector=inspector,
            inspection_type=inspection_type,
            inspection_date=inspection_date,
            location=location,
            summary=summary,
            recommendations=recommendations,
        )
        for category, description, item_status, severity, recommendation in items:
            inspection_services.add_inspection_item(
                inspection=inspection,
                category=category,
                description=description,
                status=item_status,
                severity=severity,
                recommendation=recommendation,
            )
        if target_status == "COMPLETED":
            inspection_services.complete_inspection(inspection=inspection)
        elif target_status == "IN_PROGRESS":
            inspection_services.update_inspection(
                inspection=inspection, data={"status": "IN_PROGRESS"}
            )
        inspections.append(inspection)

    print(
        f"Seeded {len(INSPECTIONS)} inspections (2 COMPLETED — one OBSERVATION, "
        "one FAIL — and 1 IN_PROGRESS)"
    )

    for title, description, evidence_type, file_builder, captured_at, inspection_index in EVIDENCE:
        inspection_services.create_evidence(
            project=project,
            uploaded_by=inspector,
            uploaded_file=file_builder(),
            evidence_type=evidence_type,
            inspection=inspections[inspection_index] if inspection_index is not None else None,
            title=title,
            description=description,
            captured_at=captured_at,
        )

    print(f"Seeded {len(EVIDENCE)} evidence files (2 inspection-linked, 2 standalone)")


def _seed_folders_and_documents(project: Project, uploaded_by: User) -> None:
    folders_by_name = {}
    for name, description, parent_name in FOLDERS:
        folder = document_services.create_folder(
            project=project,
            name=name,
            description=description,
            parent=folders_by_name.get(parent_name),
        )
        folders_by_name[name] = folder

    print(f"Seeded {len(FOLDERS)} document folders (including one nested subfolder)")

    for name, document_type, folder_name, file_builder, version_notes in DOCUMENTS:
        document = document_services.create_document(
            project=project,
            uploaded_by=uploaded_by,
            uploaded_file=file_builder(),
            document_type=document_type,
            folder=folders_by_name.get(folder_name),
            name=name,
        )
        for change_notes in version_notes:
            document = document_services.create_new_version(
                previous=document,
                uploaded_by=uploaded_by,
                uploaded_file=_pdf(f"{name.lower().replace(' ', '-')}-v2.pdf"),
                change_notes=change_notes,
            )

    total_versions = len(DOCUMENTS) + sum(len(v) for _, _, _, _, v in DOCUMENTS)
    print(
        f"Seeded {len(DOCUMENTS)} documents ({total_versions} total version rows — "
        "the Main Building Contract carries 2 versions)"
    )


def run() -> None:
    user = _get_or_create_demo_user()
    organization = _get_or_create_demo_organization(user)
    _ensure_membership(user, organization)

    if Project.objects.filter(
        organization=organization, project_code=PROJECT_CODE
    ).exists():
        print(
            f"Project '{PROJECT_CODE}' already exists in '{organization.name}' — "
            "nothing more to seed."
        )
        return

    project = _create_project(organization)
    _add_budget_items(project)
    _add_progress_updates(project, submitted_by=user)
    _seed_payments(project, submitter=user, reviewer=user)
    _seed_variations(project, created_by=user, approver=user)
    _seed_risks(project, owner=user)
    _seed_issues(project, owner=user)
    _seed_inspections_and_evidence(project, inspector=user)
    _seed_folders_and_documents(project, uploaded_by=user)

    print()
    print("Demo data seeded.")
    print(f"  Login:        {DEMO_USER_EMAIL} / {DEMO_USER_PASSWORD}")
    print(f"  Organization: {organization.name} ({organization.id})")
    print(f"  Project:      {project.project_code} ({project.id})")


if __name__ == "__main__":
    run()