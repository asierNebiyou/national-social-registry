# OpenG2P Registry NSR Extension

Extension package for the [OpenG2P Registry Platform](https://github.com/OpenG2P/registry-platform) that implements the domain of a **National Social Registry (NSR)**: a registry of households and the individuals in them, with their vulnerability, livelihood, land, livestock, shocks and programme enrolments, used to target and enrol people in social-protection programmes.

It adds only the NSR domain on top of the platform: the register models and schemas, the business rules run when records are saved and approved, a poverty score, and the seed metadata (register definitions, forms, approval workflow, DCI templates). The platform supplies everything else, including the APIs, change requests, approval, history and audit.

Follows the same layout as [`openg2p-registry-farmer-extension`](https://github.com/OpenG2P/farmer-registry/tree/1.2/farmer-extension).

## Registers

| Mnemonic | Table | Extends |
|---|---|---|
| `Household` | `g2p_register_households` | `G2PRegister`, `G2PGeo` |
| `Individual` | `g2p_register_individuals` | `G2PRegister`, `G2PPerson`, `G2PGeo` |

An individual belongs to a household through `link_internal_record_id`. The household's size counts (`size_total`, `size_adults`, `size_children_u5`, ...) are recalculated from its members whenever a member changes (`services/utils/household_roster.py`).

## Supporting Tables

| Mnemonic | Table | Parent (via `link_internal_record_id`) |
|---|---|---|
| `HouseholdHousingAndServices` | `g2p_register_household_housing_and_services` | Household |
| `HouseholdAsset` | `g2p_register_household_assets` | Household |
| `HouseholdProgram` | `g2p_register_household_programs` | Household |
| `IndividualVulnerability` | `g2p_register_individual_vulnerability` | Individual |
| `IndividualDisability` | `g2p_register_individual_disabilities` | Individual |
| `IndividualLivelihood` | `g2p_register_individual_livelihoods` | Individual |
| `IndividualLand` | `g2p_register_individual_land` | Individual |
| `IndividualLivestock` | `g2p_register_individual_livestock` | Individual |
| `IndividualShock` | `g2p_register_individual_shocks` | Individual |
| `IndividualProgram` | `g2p_register_individual_programs` | Individual |

Every register and supporting table has a `g2p_register_history_*` twin for version snapshots and a `g2p_intake_form_*` twin for intake form submissions.

The household poverty score (`score_compute/services/poverty.py`) is a weighted sum of household attributes, configured in `g2p_register_score_definitions`, and is stored by the platform in its score table.

> Change requests, approval (AWE), history and the audit trail are provided by the registry platform itself; we do not duplicate them here.

## Where things live

| Path (under `src/openg2p_registry_nsr_extension/`) | What it holds |
|---|---|
| `app.py` | `Initializer`: registers the domain services and creates the tables (`migrate_database`) |
| `register_domain/models/` | SQLAlchemy models; `enums.py` lists the codes each coded field accepts |
| `register_domain/schemas/` | Pydantic schemas: the fields a change request may carry |
| `register_domain/services/` | Business rules per register: `validate_domain_attributes` (on save), `pre_approve` / `post_approve`, record names and search text |
| `meta_data/` | Seed SQL: register definitions, sections, UI tabs, intake forms, score definitions, DCI message rules |
| `awe_meta_data/` | Approval workflow seed (policy, stages, approver rules) |
| `templates/` | Jinja templates mapping DCI / CRVS payloads to and from an NSR individual |
| `ingestion_pipeline/` | Enrichers used when records are ingested in bulk |

## Dropdown values come from Master Data

Code lists (gender, relationship to head, dwelling type, programme name, ...) are served by the **Master Data Service (MDS)**, which loads them from a country pack in [openg2p-data](https://github.com/OpenG2P/openg2p-data) (`packs/<COUNTRY>/codelists/*.json`). The registry reads them from MDS through its API, never from MDS's database.

`register_domain/models/enums.py` is the list of codes the NSR model accepts for each coded field. When a code list changes in the country pack, change the matching enum too, or values staff can pick will be rejected.

The head of a household is marked with the `is_head` yes/no field, not with a `SELF` relationship, which the country pack does not have (NSR-07).

## Install (from source)

```bash
pip install nsr-extension/
```

The package installs under its own import name, `openg2p_registry_nsr_extension`. The registry images select it at runtime with `REGISTRY_EXTENSION_MODULE=openg2p_registry_nsr_extension` (see `docker/*/Dockerfile`), so it can sit beside the platform's reference extension in one image.

For local development, install it editable into an environment that already has the registry platform (`openg2p-registry-core`) installed:

```bash
pip install -e 'nsr-extension[test]'
```

## Running the tests

The unit tests in `nsr-extension/tests/` import the registry platform, so run them where `openg2p-registry-core` is installed:

```bash
pip install -e 'nsr-extension[test]'
python -m pytest nsr-extension/tests -q
```

Without a local platform install, run them the way CI does, inside the pinned platform image:

```bash
RP_VERSION=$(sed -n 's/^ARG RP_VERSION=//p' docker/staff-api/Dockerfile)
docker run --rm --user 0 -v "$PWD:/src" -w /src --entrypoint sh \
  "openg2p/openg2p-registry-staff-api:${RP_VERSION}" -c \
  "pip install --quiet -e 'nsr-extension[test]' && python -m pytest nsr-extension/tests -q"
```

The repository-level checks need only pytest: `python -m pytest test/test_rp_pin_lockstep.py test/test_enum_values.py -q`. The end-to-end sanity suite in `test/sanity/` runs against an install, not locally.
