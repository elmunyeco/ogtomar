from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class RecipeMedicationLimits:
    """Operational RCTA limits kept outside the user interface."""

    per_document: int
    max_documents: int

    @property
    def max_medications(self) -> int:
        return self.per_document * self.max_documents


def recipe_medication_limits() -> RecipeMedicationLimits:
    # Innovamed's Swagger does not publish maxItems. HML was observed splitting
    # ten medications into 3 + 3 + 3 + 1 documents on 2026-09-18.
    per_document = max(1, int(getattr(settings, "QBI2_MEDICATIONS_PER_DOCUMENT", 3)))
    max_documents = max(1, int(getattr(settings, "QBI2_MAX_DOCUMENTS_PER_REQUEST", 3)))
    return RecipeMedicationLimits(
        per_document=per_document,
        max_documents=max_documents,
    )


def validate_recipe_medication_count(count: int) -> RecipeMedicationLimits:
    limits = recipe_medication_limits()
    if count < 1:
        raise ValueError("Debe seleccionar al menos un medicamento.")
    if count > limits.max_medications:
        raise ValueError(
            f"La operación admite hasta {limits.max_medications} medicamentos "
            f"en un máximo de {limits.max_documents} recetas de RCTA."
        )
    return limits
