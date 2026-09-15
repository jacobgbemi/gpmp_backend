Build Backend Stage 3 of GlintPM Private.

Follow:

Business problem
→ Data model
→ API
→ Implementation
→ Tests
→ Postman
→ Frontend
→ Failure states
→ Database integrity
→ Security
→ Git
→ Documentation

========================================
1. BUSINESS PROBLEM
========================================

Construction projects change.

GlintPM Private must help an owner understand:

- what has changed
- why it changed
- how much it may cost
- whether the change is approved
- what risks threaten the project
- what issues require action

The system must distinguish between proposed exposure and approved financial impact.

========================================
2. DATA MODEL
========================================

Variation:

- UUID
- project
- variation number
- title
- description
- reason
- category
- requested amount
- estimated amount
- approved amount
- status
- dates
- created/approved by

Statuses:

PROPOSED
UNDER_REVIEW
APPROVED
REJECTED
IMPLEMENTED
CLOSED

IMPORTANT:

Only APPROVED variations affect the project's approved budget.

Risk:

- UUID
- project
- title
- description
- probability 1–5
- impact 1–5
- risk_score
- response
- mitigation
- contingency
- owner
- status
- target date

Risk score:

probability × impact

Issue:

- UUID
- project
- title
- description
- severity
- owner
- status
- target date
- resolution

========================================
3. API
========================================

Create APIs for:

/api/projects/{id}/variations/
/api/projects/{id}/risks/
/api/projects/{id}/issues/

Support:

list
retrieve
create
update
filter
status changes

========================================
4. IMPLEMENTATION
========================================

Implement services for:

Variation approval
Risk scoring
Issue status management

Ensure approved variation logic updates the appropriate project financial state without treating proposed variations as approved cost.

Use database transactions where required.

========================================
5. TESTS
========================================

Test:

- variation lifecycle
- approved variation budget impact
- rejected variation
- duplicate variation numbers
- risk score
- invalid probability/impact
- issue lifecycle
- permissions
- organization isolation

========================================
6. POSTMAN
========================================

Test complete workflows:

Create variation
→ review
→ approve
→ verify project budget

Create risk
→ calculate score
→ update status

Create issue
→ assign owner
→ resolve

Add environment variables for IDs.

========================================
7. FRONTEND
========================================

Build:

- Variations page
- Variation detail
- Risks page
- Risk detail
- Risk matrix
- Issues page

Risk matrix must visually represent probability × impact.

========================================
8. FAILURE STATES
========================================

Test:

- approving invalid variation
- modifying approved variation incorrectly
- invalid risk scores
- missing owner
- invalid status transition
- unauthorized update
- nonexistent project
- duplicate variation number

========================================
9. DATABASE INTEGRITY
========================================

Use DBeaver to verify:

- variation/project relationships
- risk/project relationships
- issue/project relationships
- approved amount calculations
- constraints
- indexes

Verify rejected/proposed variations do not incorrectly increase approved budget.

========================================
10. SECURITY
========================================

Test:

- role restrictions
- project access
- organization isolation
- IDOR
- unauthorized approvals
- unauthorized risk modification

Approval authority must be enforced by backend permissions.

========================================
11. GIT
========================================

Commit:

feat(backend): add variations risks and issues

========================================
12. DOCUMENTATION
========================================

Document:

- variation lifecycle
- approved variation rule
- risk scoring formula
- issue lifecycle
- authorization rules

========================================
13. ADD TO UNFOLD ADMIN
========================================
Variation
Risk
Issue