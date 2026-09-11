"""Tests for configuration validation."""

from free_claude_code.api.config_validation import (
    ValidationError,
    ValidationResult,
    validate_config,
)


class TestValidationError:
    """Test ValidationError dataclass."""

    def test_validation_error_creation(self):
        """Test creating a validation error."""
        error = ValidationError(
            field="provider_key",
            message="Missing API key",
            severity="error",
        )
        assert error.field == "provider_key"
        assert error.message == "Missing API key"
        assert error.severity == "error"


class TestValidationResult:
    """Test ValidationResult dataclass and methods."""

    def test_valid_result_to_dict(self):
        """Test converting a valid result to dict."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
        )
        data = result.to_dict()

        assert data["is_valid"] is True
        errors = data["errors"]
        assert isinstance(errors, list)
        assert errors == []
        warnings = data["warnings"]
        assert isinstance(warnings, list)
        assert warnings == []
        assert data["error_count"] == 0
        assert data["warning_count"] == 0

    def test_invalid_result_to_dict(self):
        """Test converting an invalid result to dict."""
        error = ValidationError(
            field="api_key",
            message="Required field missing",
            severity="error",
        )
        warning = ValidationError(
            field="url",
            message="Invalid format",
            severity="warning",
        )
        result = ValidationResult(
            is_valid=False,
            errors=[error],
            warnings=[warning],
        )
        data = result.to_dict()

        assert data["is_valid"] is False
        errors = data["errors"]
        assert isinstance(errors, list)
        assert len(errors) == 1
        error_dict = errors[0]
        assert isinstance(error_dict, dict)
        assert error_dict["field"] == "api_key"
        assert error_dict["message"] == "Required field missing"
        warnings_list = data["warnings"]
        assert isinstance(warnings_list, list)
        assert len(warnings_list) == 1
        assert data["warning_count"] == 1


class TestValidateConfig:
    """Test configuration validation."""

    def test_empty_config_valid(self):
        """Test that empty config is valid."""
        result = validate_config({})

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_url_passes(self):
        """Test that valid URLs pass validation."""
        result = validate_config(
            {
                "provider_url": "https://api.example.com",
                "backup_url": "http://localhost:8000",
            }
        )

        assert result.is_valid is True
        assert not any(w.field == "provider_url" for w in result.warnings)

    def test_invalid_url_format_warning(self):
        """Test that invalid URL format produces a warning."""
        result = validate_config(
            {
                "provider_url": "not-a-url",
            }
        )

        assert result.is_valid is True  # Not an error, just a warning
        assert len(result.warnings) > 0
        assert any("should be a valid URL" in w.message for w in result.warnings)

    def test_model_without_providers_warning(self):
        """Test that selecting model without enabled providers produces warning."""
        result = validate_config(
            {
                "model": "gpt-4",
            }
        )

        assert result.is_valid is True
        assert any("no providers are enabled" in w.message for w in result.warnings)

    def test_model_with_enabled_provider_no_warning(self):
        """Test that model with enabled provider doesn't warn."""
        result = validate_config(
            {
                "model": "gpt-4",
                "provider_openai_enabled": True,
            }
        )

        assert result.is_valid is True
        assert not any("no providers are enabled" in w.message for w in result.warnings)

    def test_multiple_validation_issues(self):
        """Test config with multiple validation issues."""
        result = validate_config(
            {
                "model": "gpt-4",
                "bad_url": "not-a-url",
            }
        )

        assert result.is_valid is True
        assert len(result.warnings) >= 2

    def test_validation_result_structure(self):
        """Test the structure of validation results."""
        result = validate_config(
            {
                "provider_url": "invalid",
            }
        )

        # Verify the result can be serialized
        data = result.to_dict()
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data
        assert "error_count" in data
        assert "warning_count" in data
        errors = data["errors"]
        assert isinstance(errors, list)
        warnings = data["warnings"]
        assert isinstance(warnings, list)


class TestValidateConfigIntegration:
    """Integration tests for config validation."""

    def test_realistic_valid_config(self):
        """Test validation of realistic valid configuration."""
        config = {
            "model": "gpt-4",
            "provider_openai_enabled": True,
            "provider_openai_url": "https://api.openai.com/v1",
            "temperature": 0.7,
        }
        result = validate_config(config)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_realistic_config_with_warnings(self):
        """Test validation of realistic configuration with warnings."""
        config = {
            "model": "gpt-4",
            "provider_url": "localhost:8000",  # Invalid URL format
        }
        result = validate_config(config)

        assert result.is_valid is True  # Warnings don't make it invalid
        assert len(result.warnings) > 0

    def test_validation_preserves_error_details(self):
        """Test that validation preserves error details."""
        result = validate_config({})

        # Get a dict representation and verify all fields are present
        data = result.to_dict()
        errors = data["errors"]
        assert isinstance(errors, list)
        for error in errors:
            assert isinstance(error, dict)
            assert "field" in error
            assert "message" in error

        warnings = data["warnings"]
        assert isinstance(warnings, list)
        for warning in warnings:
            assert isinstance(warning, dict)
            assert "field" in warning
            assert "message" in warning
