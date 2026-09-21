"""
Shared field validators for business-domain models.

Centralized here so every app enforces the same rules for money and
percentage fields rather than re-declaring `MinValueValidator(0)` inline
everywhere.
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator

# Money fields (budgets, payments, variations, ...) must never be negative.
# A refund/credit, if ever needed, is modeled as an explicit adjustment
# record, not a negative amount on the original field.
MONEY_VALIDATORS = [MinValueValidator(Decimal(0))]

# Percentage fields (progress, completion, etc.) are bounded 0-100.
PERCENT_VALIDATORS = [MinValueValidator(Decimal(0)), MaxValueValidator(Decimal(100))]
