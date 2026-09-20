"""Configuration validation utilities for the admin API."""

from collections.abc import Mapping
from dataclasses import dataclass

from free_claude_code.config.admin.values import load_value_state
from free_claude_code.config.provider_catalog import PROVIDER_CATALOG
from free_claude_code.core.json_types import JsonValue


@dataclass
class ValidationError:
    """Represents a single validation error."""

    field: str
    message: str
    severity: str  # "error" or "warning"


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]

    def to_dict(self) -> dict[str, object]:
        """Convert to JSON-serializable dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": [{"field": e.field, "message": e.message} for e in self.errors],
            "warnings": [
                {"field": w.field, "message": w.message} for w in self.warnings
            ],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


def validate_config(values: Mapping[str, JsonValue]) -> ValidationResult:
    """
    Validate configuration before applying.

    Checks:
    - Required provider API keys are set
    - Provider configuration is valid
    - No conflicting settings
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    # Get current state for comparison
    current_state = load_value_state()

    # Validate provider configurations
    for provider_config in PROVIDER_CATALOG.values():
        # Skip providers with no credential requirement
        if not provider_config.credential_attr:
            continue

        # Build the field name for this provider's credential
        credential_field = provider_config.credential_attr
        credential_value = values.get(credential_field)

        # Check if credential is empty when required
        is_empty = credential_value is None or (
            isinstance(credential_value, str) and not credential_value.strip()
        )
        current_value = current_state.get(credential_field)
        if is_empty and current_value is not None and current_value.value is None:
            # Provider requires credential but none is configured
            errors.append(
                ValidationError(
                    field=credential_field,
                    message=f"{provider_config.display_name} requires credentials to be configured",
                    severity="error",
                )
            )

    # Validate string fields are not empty when required
    for field_key, field_value in values.items():
        if (
            isinstance(field_value, str)
            and field_key.endswith("_url")
            and field_value
            and not (
                field_value.startswith("http://") or field_value.startswith("https://")
            )
        ):
            # URL fields should be valid URLs if provided
            warnings.append(
                ValidationError(
                    field=field_key,
                    message=f"{field_key} should be a valid URL (starting with http:// or https://)",
                    severity="warning",
                )
            )

    # Check for conflicting settings
    model_field = values.get("model")
    if model_field and isinstance(model_field, str):
        # Check if the selected model is available from any provider
        provider_has_model = any(
            values.get(provider_id)
            for provider_id in values
            if provider_id.startswith("provider_") and provider_id.endswith("_enabled")
        )

        if not provider_has_model:
            warnings.append(
                ValidationError(
                    field="model",
                    message="Selected model but no providers are enabled",
                    severity="warning",
                )
            )

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
    )
