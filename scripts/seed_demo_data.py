"""
Demo data seed script.

Stage 0 intentionally has no business-domain models (Organization, Project,
Budget, etc.) to seed yet — this script is a placeholder so the `scripts/`
convention exists from the start.

Once the `organizations` and `projects` apps land, this will create:
    - Organization: "GlintPM Private Demo"
    - Project: "Luxury Residence — Lekki" (NGN 500,000,000)
    - budget items, progress updates, payment applications, variations,
      risks, milestones, inspections, evidence, contractor performance

Run with:
    python manage.py shell -c "import scripts.seed_demo_data as s; s.run()"
"""


def run():
    print(
        "No business-domain models exist yet (Stage 0 foundation only). "
        "Demo data seeding will be implemented once the organizations/ "
        "and projects/ apps are built."
    )


if __name__ == "__main__":
    run()
