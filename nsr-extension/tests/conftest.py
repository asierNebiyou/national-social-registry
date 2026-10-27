# Load the domain models before any test imports a service, the same order the
# app uses (app.py imports .register_domain.models first). The models import the
# services package at module level and some services import ..models back, so
# importing a service first fails with a circular import.
import openg2p_registry_nsr_extension.register_domain.models  # noqa: F401
