# GlintPM Private --- Use Cases

## 1. Purpose

Use cases describe how users interact with the system to accomplish
meaningful business outcomes.

## UC-001 --- Create a Project

**Primary actor:** Project Manager

**Goal:** Establish a project in the system.

**Preconditions:** - User is authenticated. - User has project-creation
permission.

**Main flow:** 1. User opens project creation. 2. User enters required
project information. 3. System validates input. 4. System creates the
project. 5. System returns confirmation. 6. Audit information is
recorded where required.

**Alternative flows:** - Invalid input → validation errors. - Duplicate
project/reference → system prevents or flags duplicate. - Database
failure → transaction does not leave an invalid partial record.

------------------------------------------------------------------------

## UC-002 --- Establish a Project Baseline

**Primary actor:** Project Controls Manager / authorized Planner

**Goal:** Establish an approved reference plan.

**Main flow:** 1. User selects the project. 2. User selects or imports
planning information. 3. System validates the data. 4. User reviews the
baseline. 5. Authorized user approves/establishes the baseline. 6.
System records baseline status and relevant audit information.

**Key control:** Baseline establishment should be permission-controlled
and traceable.

------------------------------------------------------------------------

## UC-003 --- Update Project Progress

**Primary actor:** Planner / authorized project team member

**Goal:** Record current project progress.

**Main flow:** 1. User selects reporting period. 2. User enters/imports
progress. 3. System validates data. 4. System stores the update. 5.
System calculates or exposes relevant variance. 6. Authorized users can
review the result.

------------------------------------------------------------------------

## UC-004 --- Analyze Schedule Variance

**Primary actor:** Planner / Project Controls Manager

**Goal:** Identify differences between baseline/planned and current
schedule performance.

**Main flow:** 1. User selects project and reporting period. 2. System
retrieves relevant schedule data. 3. System compares appropriate plan
and actual/current values. 4. System identifies variance. 5. User
investigates affected activities. 6. User records action or decision
where necessary.

------------------------------------------------------------------------

## UC-005 --- Monitor Cost Performance

**Primary actor:** Cost Engineer / Project Controls Manager

**Goal:** Understand budget, actual, and forecast cost.

**Main flow:** 1. User selects project. 2. System retrieves authorized
cost information. 3. System presents budget/actual/forecast information.
4. System highlights significant variance. 5. User investigates
underlying records. 6. User records required action.

------------------------------------------------------------------------

## UC-006 --- Manage Risk

**Primary actor:** Project Manager

**Goal:** Record and control project risks.

**Main flow:** 1. User identifies a risk. 2. User records description
and relevant attributes. 3. User assigns owner. 4. User records
mitigation/action. 5. System tracks status and due dates. 6. User
reviews risk during reporting.

------------------------------------------------------------------------

## UC-007 --- Manage Change/Variation

**Primary actor:** Project Manager / Commercial user

**Goal:** Track project changes and their potential impact.

**Main flow:** 1. User records change. 2. System assigns identifier. 3.
User records schedule/cost implications. 4. User records approval
status. 5. Authorized stakeholders review. 6. Change status is updated.
7. Approved changes can feed appropriate project-control processes.

------------------------------------------------------------------------

## UC-008 --- Produce Project Report

**Primary actor:** Project Manager / Project Controls Manager

**Goal:** Produce a reliable project performance report.

**Main flow:** 1. User selects reporting period. 2. System retrieves
relevant project data. 3. System calculates/presents approved metrics.
4. User reviews exceptions. 5. User adds required narrative. 6. Report
is generated/exported.

------------------------------------------------------------------------

## UC-009 --- Executive Project Review

**Primary actor:** Project Director / Executive

**Goal:** Quickly understand project condition.

**Main flow:** 1. User signs in. 2. User views portfolio/project
dashboard. 3. System displays relevant KPIs and exceptions. 4. User
drills into areas requiring attention. 5. User reviews underlying
evidence where permitted. 6. User makes or assigns decisions/actions.

------------------------------------------------------------------------

## UC-010 --- Investigate an Exception

**Primary actor:** Project Controls Manager

**Goal:** Understand why a project metric is outside an expected
threshold.

**Main flow:** 1. System identifies an exception. 2. User opens the
exception. 3. System displays relevant supporting information. 4. User
traces contributing records. 5. User records cause/observation where
appropriate. 6. User assigns action. 7. Action is tracked to completion.

------------------------------------------------------------------------

## UC-011 --- AI-Assisted Project Analysis

**Primary actor:** Authorized Project Manager / Project Controls user

**Goal:** Use AI to accelerate analysis of available project data.

**Main flow:** 1. User requests analysis. 2. System retrieves only
authorized data. 3. AI analyzes the permitted context. 4. System
presents findings with appropriate limitations. 5. User reviews
findings. 6. User decides whether action is required.

**Control principle:** AI output should not be treated as authoritative
without appropriate human review.
