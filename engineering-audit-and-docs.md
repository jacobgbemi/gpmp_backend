You are acting as a Senior Software Architect, Backend Engineer, Frontend Engineer, QA Engineer, Security Engineer, and Technical Product Reviewer.

Your task is to thoroughly study the existing codebase before making any recommendations.

IMPORTANT:
Do NOT assume the application is well designed simply because it runs or looks good.
Do NOT rewrite the application just because you find something you would personally implement differently.
Do NOT blindly trust comments, existing README documentation, variable names, or AI-generated code.

Your first responsibility is to understand what actually exists in the codebase.

PROJECT CONTEXT

This project is being developed as a serious production-oriented software product, not merely a prototype or AI-generated demo.

The long-term objective is to build reliable business software that can support real users, real data, real workflows, and potentially business-critical project information.

The project may use AI heavily during development, but AI-generated code must still be treated as code that requires engineering review, validation, testing, security review, and ownership.

The engineering principle is:

"AI can generate the code. Engineers must own the system."

--------------------------------------------------
PHASE 1 — STUDY THE EXISTING CODEBASE
--------------------------------------------------

Start by inspecting the entire repository.

Before changing anything, identify:

1. Technology stack
   - Frontend framework
   - Backend framework
   - Programming languages
   - Database
   - Authentication mechanism
   - API architecture
   - State management
   - UI framework/components
   - Third-party services
   - Deployment/infrastructure configuration
   - Testing frameworks
   - Package/dependency management

2. Repository structure
   Explain:
   - Major directories
   - Purpose of each directory
   - Important files
   - Entry points
   - Configuration files
   - Environment configuration
   - Database-related files
   - API-related files
   - Authentication/authorization files
   - Test files
   - Deployment files

3. Application architecture

Determine what architecture the code ACTUALLY implements.

Do not describe the architecture based only on the README.

Trace the actual flow:

User
→ Frontend
→ API
→ Business logic
→ Database
→ External services

Document where appropriate.

4. Data model

Identify:
- Main entities
- Relationships
- Primary keys
- Foreign keys
- Constraints
- Required vs optional fields
- Audit fields
- Soft deletion, if any
- Versioning, if any
- Data validation
- Potential normalization problems
- Potential integrity problems

Explain whether the current data model appears capable of supporting the intended business workflows.

5. Business logic

Identify where business rules currently live.

Determine whether logic is:
- Properly centralized
- Duplicated
- Hidden inside UI components
- Hidden inside API endpoints
- Hidden inside database queries
- Missing entirely

Identify important business rules that appear to be assumed but are not actually enforced.

--------------------------------------------------
PHASE 2 — CRITICALLY REVIEW THE SYSTEM
--------------------------------------------------

Review the codebase as if you were preparing it for a real production deployment.

Do NOT focus only on whether the application currently works.

Evaluate the following categories.

A. BUSINESS REQUIREMENTS

Ask:

- What problem does this application actually solve?
- Is that problem clearly represented in the architecture?
- Which workflows are implemented?
- Which workflows are incomplete?
- Which important workflows are missing?
- Are business rules explicitly represented?
- Are there assumptions that exist only in the developer's head?

Identify any mismatch between the intended product and the implemented system.

B. ARCHITECTURE

Evaluate:

- Separation of concerns
- Modularity
- Coupling
- Cohesion
- Scalability
- Maintainability
- Extensibility
- Error handling
- API design
- Frontend/backend boundaries
- Dependency management

Identify architectural decisions that may become problems as the system grows.

C. DATABASE

Review:

- Schema design
- Relationships
- Constraints
- Indexes
- Data types
- Nullability
- Referential integrity
- Duplicate data
- Transaction handling
- Migration strategy
- Concurrency concerns
- Auditability
- Data deletion behavior

Ask:

"What could cause the database to contain incorrect information even though the application appears to work?"

D. SECURITY

Review:

- Authentication
- Authorization
- Role-based permissions
- Object-level permissions
- Tenant/data isolation where applicable
- Password handling
- Secrets management
- API security
- Input validation
- SQL injection risks
- XSS risks
- CSRF
- CORS
- File upload security
- Sensitive information exposure
- Error-message leakage
- Dependency vulnerabilities
- Rate limiting
- Logging of sensitive information

Identify both current vulnerabilities and future security concerns.

Do not claim something is secure simply because no obvious vulnerability was found.

Clearly distinguish:

PASS
CONCERN
NOT IMPLEMENTED
NOT VERIFIED

E. FAILURE MODES

For every major workflow, ask:

"What happens when this fails?"

Examples:

- Database unavailable
- API unavailable
- Network request fails
- User submits invalid data
- User submits duplicate data
- User refreshes during an operation
- Two users modify the same record
- External service fails
- Background process fails
- File upload fails
- Authentication expires
- Permission changes while a user is active
- Deployment fails
- Migration fails

Document important failure states that are currently unhandled.

F. DATA INTEGRITY

Determine:

- Can users create impossible states?
- Can records become orphaned?
- Can totals become inconsistent?
- Can users bypass validation?
- Are calculations performed consistently?
- Are important values derived from authoritative data?
- Is there an audit trail for important changes?

For business-critical data, identify what should be immutable, versioned, approved, or auditable.

G. TESTING

Inspect the actual tests.

Do not count the existence of a test directory as adequate testing.

Determine:

- What is tested?
- What is not tested?
- Unit test coverage areas
- Integration testing
- API testing
- Authentication testing
- Permission testing
- Database integrity testing
- Failure-state testing
- Frontend testing
- End-to-end testing

Identify critical workflows that currently have no meaningful automated tests.

H. OBSERVABILITY

Review:

- Logging
- Error tracking
- Audit logs
- Monitoring
- Performance monitoring
- Health checks
- System diagnostics

Ask:

"If something goes wrong in production, can an engineer determine what happened?"

I. PERFORMANCE AND SCALABILITY

Look for:

- N+1 queries
- Inefficient database queries
- Excessive API calls
- Large payloads
- Unnecessary frontend rendering
- Missing pagination
- Missing indexes
- Blocking operations
- Poor caching strategy

Do not prematurely optimize.

Identify only realistic bottlenecks and explain why they matter.

J. DEPLOYMENT AND OPERATIONS

Review:

- Environment configuration
- Development/staging/production separation
- Secrets
- Database migrations
- Build process
- Deployment process
- Rollback strategy
- Backups
- Recovery strategy
- CI/CD
- Health checks

Ask:

"Could another competent engineer deploy and maintain this system without asking the original developer how everything works?"

--------------------------------------------------
PHASE 3 — AI-GENERATED CODE REVIEW
--------------------------------------------------

Because AI may have been used to develop parts of this application, specifically look for patterns commonly produced by AI-assisted coding:

- Duplicate implementations
- Over-abstraction
- Inconsistent naming
- Inconsistent architecture
- Unnecessary dependencies
- Dead code
- Placeholder functionality
- Mock data accidentally used in production paths
- Weak error handling
- Hardcoded values
- Security shortcuts
- Business logic duplicated across layers
- Components/functions that are too large
- Code that appears correct but lacks tests
- Comments that do not match implementation
- "TODO" functionality presented as complete
- Fake/demo integrations
- Inconsistent API contracts

Do not assume code is AI-generated. Report these as engineering concerns, not accusations.

--------------------------------------------------
PHASE 4 — REQUIREMENTS VS CURRENT IMPLEMENTATION
--------------------------------------------------

Create a clear comparison:

REQUIREMENT
CURRENT IMPLEMENTATION
STATUS
EVIDENCE
GAP
RECOMMENDED NEXT STEP

Use these status categories:

- COMPLETE
- PARTIALLY COMPLETE
- NOT IMPLEMENTED
- NEEDS VERIFICATION
- TECHNICAL DEBT

Do not mark something COMPLETE merely because related code exists.

It should be considered complete only if the implementation, validation, and relevant testing support that conclusion.

--------------------------------------------------
PHASE 5 — RISK REGISTER
--------------------------------------------------

Create a technical risk register.

For each significant risk include:

- Risk
- Category
- Evidence
- Impact
- Likelihood
- Severity
- Current mitigation
- Recommended mitigation
- Priority

Use:

CRITICAL
HIGH
MEDIUM
LOW

Do not assign severity arbitrarily. Explain the reasoning.

Pay particular attention to:

- Security
- Data loss
- Data corruption
- Incorrect business calculations
- Unauthorized access
- Lack of auditability
- Production failure
- Poor maintainability
- Scalability limitations

--------------------------------------------------
PHASE 6 — ENGINEERING MATURITY ASSESSMENT
--------------------------------------------------

Do NOT provide a generic score such as "8/10".

Instead, describe the maturity of each area:

1. Product requirements
2. Architecture
3. Database design
4. Backend
5. Frontend
6. API design
7. Security
8. Authentication
9. Authorization
10. Testing
11. Data integrity
12. Observability
13. Deployment
14. Documentation
15. Maintainability

For each area provide:

CURRENT STATE
EVIDENCE
GAP
WHAT GOOD LOOKS LIKE
NEXT ACTION

Avoid overall rankings or vague statements.

--------------------------------------------------
PHASE 7 — RECOMMENDED ENGINEERING ROADMAP
--------------------------------------------------

Based on the actual codebase, create a practical roadmap.

Separate it into:

PHASE 0 — Understanding and requirements
PHASE 1 — Foundation
PHASE 2 — Data integrity
PHASE 3 — Backend/API
PHASE 4 — Authentication and authorization
PHASE 5 — Frontend
PHASE 6 — Testing
PHASE 7 — Security hardening
PHASE 8 — Observability
PHASE 9 — Deployment
PHASE 10 — Production readiness

For each phase explain:

- What needs to be done
- Why it matters
- Dependencies
- What should be tested
- Definition of done

Do not recommend rebuilding everything unless the evidence shows that the existing architecture cannot reasonably support the product.

--------------------------------------------------
PHASE 8 — UPDATE README.md
--------------------------------------------------

After completing the audit, update the repository's README.md.

The README should become an accurate engineering document, not marketing copy.

IMPORTANT:

Do not simply append the audit to the existing README.

Restructure it where necessary so that a new engineer can understand:

1. What the project is
2. What problem it solves
3. Current project status
4. Technology stack
5. Architecture
6. Repository structure
7. Core entities/data model
8. Major workflows
9. API structure
10. Authentication/authorization
11. Development setup
12. Environment variables
13. Database setup
14. Running the application
15. Testing
16. Security considerations
17. Known limitations
18. Technical debt
19. Current risks
20. Engineering roadmap
21. Important architectural decisions
22. Deployment considerations
23. Contribution/development guidelines

Clearly separate:

CURRENTLY IMPLEMENTED

from

PLANNED

and

NOT YET VERIFIED.

Never document planned functionality as if it already exists.

--------------------------------------------------
README ENGINEERING PRINCIPLE
--------------------------------------------------

The README must answer these questions for a new engineer:

"What exists?"

"How does it work?"

"Why was it designed this way?"

"What is incomplete?"

"What can fail?"

"What must I be careful about?"

"How do I test it?"

"How do I safely change it?"

"What technical debt exists?"

"What should be built next?"

--------------------------------------------------
PHASE 9 — DO NOT HIDE PROBLEMS
--------------------------------------------------

Do not modify the README to make the project look better than it actually is.

If you discover:

- poor architecture
- missing tests
- security concerns
- incomplete functionality
- questionable database design
- technical debt
- undocumented assumptions
- scalability concerns

document them honestly.

The purpose of the README is to create an accurate engineering baseline.

--------------------------------------------------
PHASE 10 — FINAL REPORT
--------------------------------------------------

After updating README.md, provide a concise summary containing:

1. What you inspected
2. Major strengths
3. Major engineering concerns
4. Critical unknowns
5. Important security concerns
6. Important data-integrity concerns
7. Testing gaps
8. Architecture concerns
9. Changes made to README.md
10. Recommended immediate next steps

IMPORTANT:

Do not make code changes unless explicitly instructed.

Your task in this pass is:

AUDIT → CRITIQUE → DOCUMENT → UPDATE README.md

The README must reflect the REAL current state of the codebase.

If you cannot verify something from the repository, explicitly state:

"NOT VERIFIED"

rather than guessing.