Build Backend Stage 4 of GlintPM Private.

Follow the complete 12-step workflow.

========================================
1. BUSINESS PROBLEM
========================================

Owners need evidence, not just statements.

GlintPM Private must allow project teams to record:

- inspections
- site observations
- payment verification evidence
- progress evidence
- milestone evidence
- project documents
- photos/videos/documents

The evidence should support independent project assurance.

========================================
2. DATA MODEL
========================================

Create:

Inspection
InspectionItem
ProjectEvidence
DocumentFolder
Document

Inspection types:

ROUTINE
PAYMENT_VERIFICATION
PROGRESS_VERIFICATION
QUALITY
MILESTONE
SPECIAL

Inspection item statuses:

PASS
FAIL
OBSERVATION
NOT_APPLICABLE

Evidence types:

PHOTO
VIDEO
DOCUMENT
SCREENSHOT
OTHER

Documents should support basic versioning.

========================================
3. API
========================================

Create:

/api/projects/{id}/inspections/
/api/inspections/{id}/
/api/projects/{id}/evidence/
/api/projects/{id}/documents/
/api/documents/{id}/

Support secure uploads.

========================================
4. IMPLEMENTATION
========================================

Implement:

- inspection workflows
- inspection items
- evidence metadata
- document folders
- documents
- basic versions

Validate:

- file type
- file size
- ownership
- project association

Prepare architecture for cloud object storage.

Do not expose storage credentials.

========================================
5. TESTS
========================================

Test:

- inspection CRUD
- inspection item status
- evidence creation
- document upload
- invalid file types
- oversized files
- project isolation
- document versioning
- permissions

========================================
6. POSTMAN
========================================

Test:

Create inspection
→ add inspection items
→ submit evidence
→ upload document
→ retrieve document
→ create new version

Test invalid uploads.

========================================
7. FRONTEND
========================================

Build:

- Inspections
- Inspection detail
- Evidence gallery
- Documents
- Upload UI
- Document version display

Optimize inspection/evidence workflows for mobile site personnel.

========================================
8. FAILURE STATES
========================================

Test:

- unsupported file
- oversized file
- failed upload
- unauthorized file access
- nonexistent inspection
- invalid project
- duplicate version
- network interruption

========================================
9. DATABASE INTEGRITY
========================================

Using DBeaver verify:

- documents belong to correct projects
- evidence belongs to correct projects
- inspection relationships
- version relationships
- no orphan records

========================================
10. SECURITY
========================================

Perform a serious file-security review.

Check:

- upload validation
- MIME/type validation
- file size limits
- filename handling
- path traversal
- authorization
- object-level access
- project isolation
- sensitive document exposure

Backend must remain authoritative.

========================================
11. GIT
========================================

Commit:

feat(backend): add inspections evidence and documents

========================================
12. DOCUMENTATION
========================================

Document:

- evidence architecture
- upload restrictions
- document versioning
- storage strategy
- security decisions

========================================
13. ADD TO UNFOLD ADMIN
========================================
Inspection
InspectionItem
ProjectEvidence
DocumentFolder
Document