import unittest

from openg2p_registry_nsr_extension.register_domain.schemas.individual import (
    G2PIntakeFormSchemaIndividual,
    G2PRegisterSchemaIndividual,
)

# Schemas a change request or intake submission is validated against when it is
# applied. A text value here used to fail only at approval, leaving the change
# request PENDING after every stage had approved it.
SCHEMAS = [
    cls
    for cls in (G2PRegisterSchemaIndividual, G2PIntakeFormSchemaIndividual)
    if "alias_names" in cls.model_fields
]


def _validate(cls, value):
    return cls.__pydantic_validator__.validate_assignment(
        cls.model_construct(), "alias_names", value
    ).alias_names


class AliasNamesTests(unittest.TestCase):
    def test_register_schema_is_covered(self):
        self.assertIn(G2PRegisterSchemaIndividual, SCHEMAS)

    def test_single_name_from_text_box_becomes_list(self):
        for cls in SCHEMAS:
            self.assertEqual(_validate(cls, "bth"), ["bth"])

    def test_comma_separated_names_are_split_and_trimmed(self):
        for cls in SCHEMAS:
            self.assertEqual(_validate(cls, " bth, brenty ,"), ["bth", "brenty"])

    def test_blank_text_means_no_alias_names(self):
        for cls in SCHEMAS:
            self.assertIsNone(_validate(cls, ""))
            self.assertIsNone(_validate(cls, "   "))

    def test_list_and_none_are_unchanged(self):
        for cls in SCHEMAS:
            self.assertEqual(_validate(cls, ["a", "b"]), ["a", "b"])
            self.assertIsNone(_validate(cls, None))
