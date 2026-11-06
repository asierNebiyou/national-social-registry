#!/usr/bin/env python3
"""Load sample data into NSR Postgres.

Reads:
- Master Data, through its API (never its database): the geography, to resolve
  geo ids, and the country pack's sample people — see mds() below
- /openg2p-data/demography/{individuals,households}.csv (core+geo, shared), the
  fallback when Master Data carries no samples
- /seed/seed-data/*.json (NSR sub-tables, shipped in the db-seed image)
"""

import csv
import json
import os
import sys
import uuid
from datetime import date
from pathlib import Path

import psycopg2
import psycopg2.extras
from psycopg2.extras import Json


def to_json(value):
    return None if value is None else Json(value)


SEEDER = "seeder"
CREATED_AT = "2026-04-01 00:00:00"

OPENG2P_DATA_DIR = Path(os.environ.get("OPENG2P_DATA_DIR", "/openg2p-data"))
DEMO_DIR = OPENG2P_DATA_DIR / "demography"
NSR_DATA_DIR = Path(os.environ.get("NSR_SEED_DATA_DIR", "/seed/seed-data"))


def env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"[load-sample-data] Missing env var: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def load_json(path: Path):
    if not path.is_file():
        print(f"[load-sample-data] Missing file: {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


JSON_COLUMNS_INDIVIDUAL = {"phone_numbers"}
JSON_COLUMNS_HOUSEHOLD = set()

# Geo is carried in the seed files as plain names (country..village); the id the
# registry stores has to be derived from them.
#
# It is RESOLVED against master-data rather than computed, because only
# master-data knows what its own ids are. Seeded from a country pack — now the
# default — a unit's id is its P-code, so master-data holds "XK01010101" while
# the slug-path this used to compute, "kamuntu/jasiri/baraka/umani/bimaka",
# matches nothing. Nothing errors either: the names in geo_code_hierarchy_json
# still read correctly, so reports that unpack geo positionally look right, and
# the only symptom is that these records never appear on a map.
#
# Resolution walks the name chain through parent links rather than matching
# names globally, since a village name repeats under different wards.
#
# The slug-path remains as the fallback for when master-data is unreachable or
# empty, or holds a legacy slug-path geography (the retired geo.csv loader),
# whose ids ARE slug-paths. So this works against either style and never does
# worse than before; whichever path was taken is reported at the end.
GEO_LEVELS = ["country", "region", "district", "ward", "village"]


def _slug(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


# (parent unit id or "", lowercased name) -> unit id, read once from
# master-data. Empty when master-data is unreachable or unseeded, which is what
# puts every lookup on the slug-path fallback.
_GEO_INDEX: dict = {}
_GEO_STATS = {"resolved": 0, "fallback": 0, "unresolved_examples": []}


# ── Master Data, through its API ─────────────────────────────────────────────
#
# Never its database: the registry reads Master Data the way its services do,
# through MDS's /catalogue and /samples endpoints, as its own Keycloak client.
# The client is the platform's stdlib one, /seed/mds_client.py in the db-seed
# base image (MDS_API_URL, MDS_TOKEN_URL, MDS_CLIENT_ID, MDS_CLIENT_SECRET come
# from the db-seed Job). Run from a checkout, it is found in the sibling
# registry-platform repo.

def _mds_client_module():
    """(MdsClient, MdsError), or None with the reason printed."""
    try:
        from mds_client import MdsClient, MdsError  # /seed/mds_client.py
        return MdsClient, MdsError
    except ImportError:
        pass
    sibling = Path(__file__).resolve().parents[3] / "registry-platform" / "docker" / "db-seed"
    if (sibling / "mds_client.py").is_file():
        sys.path.insert(0, str(sibling))
        from mds_client import MdsClient, MdsError
        return MdsClient, MdsError
    print("[load-sample-data] MDS_API_URL is set but mds_client.py is not importable — "
          "this db-seed image predates the registry platform's Master Data API client "
          "(/seed/mds_client.py). Master Data is skipped.")
    return None


_MDS = None  # the client, once opened; False once known to be unavailable
# What a failed Master Data read raises: MdsError (incl. MdsUnavailable), and a
# malformed response. Widened once the client is imported.
_MDS_ERRORS: tuple = (OSError, ValueError)


def mds():
    """The Master Data client, or None when it is not configured or unusable.

    Best effort on purpose. No MDS_API_URL, a base image without the client, or
    an unreachable MDS all mean the same thing here — nothing to resolve
    against — and none of them should stop sample data loading.
    """
    global _MDS, _MDS_ERRORS
    if _MDS is None:
        _MDS = False
        if not os.environ.get("MDS_API_URL", "").strip():
            print("[load-sample-data] MDS_API_URL not set — no Master Data: geo ids fall "
                  "back to slug-paths and people to the demography CSV.")
        else:
            module = _mds_client_module()
            if module:
                client_cls, error_cls = module
                _MDS_ERRORS = (error_cls, OSError, ValueError)
                _MDS = client_cls.from_env()
    return _MDS or None


def load_geo_units() -> list:
    """Every active unit of the published geography, from master-data; [] if none."""
    client = mds()
    if client is None:
        return []
    try:
        return client.all_geo_units()
    except _MDS_ERRORS as exc:
        print(f"[load-sample-data] could not read master-data geo ({exc}) — slug-paths.")
        return []


def load_geo_index(units: list) -> dict:
    """Index master-data's units by (parent id, name) so a name chain resolves."""
    index = {
        (u.get("parent_unit_id") or "", str(u.get("name") or "").strip().lower()): u["unit_id"]
        for u in units
    }
    if index:
        print(f"[load-sample-data] master-data geo: {len(index)} units available for resolution.")
    return index


def load_geo_chain_by_id(units: list) -> dict:
    """unit id -> (level_mnemonic, name, parent_id), for walking upwards.

    This is what makes the loader country-agnostic. A record carries the id of
    the one unit it sits in; every level above it — and how many there are, and
    what they are called — is read from master-data rather than assumed. The
    five names this file used to hard-code, country/region/district/ward/village,
    describe Kamuntu and nothing else: Ethiopia has four levels and calls the
    middle ones zone and woreda.
    """
    if not units:
        return {}
    try:
        mnemonic = {lv["level_id"]: lv.get("level_mnemonic") for lv in mds().geo_levels()}
    except _MDS_ERRORS:
        mnemonic = {}
    return {
        u["unit_id"]: (mnemonic.get(u.get("level_id")) or u.get("level_id"),
                       u.get("name"), u.get("parent_unit_id"))
        for u in units
    }


_GEO_BY_ID: dict = {}


def hierarchy_from_pcode(pcode: str) -> dict:
    """Walk a unit's ancestry in master-data, root first."""
    chain = []
    seen, cur = set(), pcode
    while cur and cur in _GEO_BY_ID and cur not in seen:
        seen.add(cur)
        level, name, parent = _GEO_BY_ID[cur]
        chain.append({"level_mnemonic": level, "level_value_mnemonic": name,
                      "level_value_id": cur})
        cur = parent
    chain.reverse()
    return {"hierarchy": chain}


def resolve_geo_chain(rec: dict) -> list:
    """Resolve country..village names to master-data's own ids, or [] if any
    link is missing. Partial resolution is deliberately not returned: half a
    chain produces a hierarchy whose upper levels join and whose lower ones do
    not, which is harder to notice than none of it joining."""
    if not _GEO_INDEX:
        return []
    ids, parent = [], ""
    for level in GEO_LEVELS:
        name = str(rec.get(level) or "").strip().lower()
        found = _GEO_INDEX.get((parent, name))
        if not found:
            return []
        ids.append(found)
        parent = found
    return ids


def geo_ids(rec: dict) -> list:
    """One id per level — master-data's where they resolve, slug-paths where not."""
    resolved = resolve_geo_chain(rec)
    if resolved:
        _GEO_STATS["resolved"] += 1
        return resolved
    _GEO_STATS["fallback"] += 1
    if len(_GEO_STATS["unresolved_examples"]) < 3:
        _GEO_STATS["unresolved_examples"].append(
            "/".join(str(rec.get(level) or "") for level in GEO_LEVELS)
        )
    return ["/".join(_slug(rec[GEO_LEVELS[i]]) for i in range(depth + 1))
            for depth in range(len(GEO_LEVELS))]


def geo_lowest_id(rec: dict) -> str:
    """The id of the record's lowest geo unit."""
    # A record sourced from master-data already knows exactly where it is; only
    # the CSV needs its names resolved.
    if rec.get("geo_pcode"):
        return rec["geo_pcode"]
    return geo_ids(rec)[-1]


def geo_hierarchy_dict(rec: dict) -> dict:
    """Build geo_code_hierarchy_json from the name columns, matching the shape
    registry-core's G2PGeoHierarchyService produces at runtime."""
    if rec.get("geo_pcode"):
        return hierarchy_from_pcode(rec["geo_pcode"])
    ids = geo_ids(rec)
    return {
        "hierarchy": [
            {
                "level_mnemonic": level,
                "level_value_mnemonic": rec[level],
                "level_value_id": ids[depth],
            }
            for depth, level in enumerate(GEO_LEVELS)
        ]
    }


def geo_hierarchy(rec: dict):
    return to_json(geo_hierarchy_dict(rec))


def _address_line(parts) -> str:
    """One line from the pack's address parts.

    The pack's address.json declares how a country composes these properly; that
    lives in master-data's country, not here, and sample data does not warrant
    fetching it. Joining the values keeps the information rather than inventing
    a street.
    """
    if not parts:
        return ""
    return ", ".join(str(v) for v in parts.values() if v)


def load_people_from_mds() -> tuple:
    """The country's sample people, from master-data.

    Returns (individuals, households) in the same dict shape the CSV produces,
    so every insert below is unchanged — or ([], []) when master-data carries no
    samples, which is its default.

    These people belong to the country, not to this registry: master-data is
    where the country is declared, so its samples are the ones that match the
    geography and the code lists. What a registry adds on top is its own fields.
    """
    client = mds()
    if client is None:
        return [], []
    try:
        inds = client.sample_individuals()
        hhs = client.sample_households() if inds else []
    except _MDS_ERRORS as exc:
        print(f"[load-sample-data] could not read master-data samples ({exc}).")
        return [], []

    if not inds:
        return [], []

    head_of = {h["household_id"]: h.get("head_individual_id") for h in hhs}
    by_hh = {}
    for i in inds:
        by_hh.setdefault(i.get("household_id"), []).append(i)

    individuals = []
    for i in inds:
        # The registry's columns are first/middle/last. A pack that names people
        # as given name + father's name maps onto first + last; middle stays
        # empty rather than being filled with something the country does not use.
        individuals.append({
            "internal_record_id": i["individual_id"],
            "functional_record_id": i["individual_id"],
            "household_id": i.get("household_id"),
            "full_name": i.get("full_name"),
            "first_name": i.get("given_name"),
            "middle_name": None,
            "last_name": i.get("fathers_name"),
            "given_name": i.get("given_name"),
            "gender": i.get("gender"),
            # birth_date and estimated_age are alternatives (the registry
            # rejects both): a person's age is either DOCUMENTED by a full
            # birth_date or ESTIMATED. The pack carries a full birth_date;
            # older packs carry only birth_year, which is an estimate, not a
            # date — so those people get estimated_age instead of a made-up
            # 1 January birthday.
            **_age_fields(i),
            "marital_status": i.get("marital_status"),
            "education_level": i.get("education_level"),
            "foundational_id": i.get("national_id"),
            "foundational_id_masked": None,
            "phone_numbers": ([{"type": "personal", "number": i["phone"], "is_primary": True}]
                              if i.get("phone") else None),
            "emails": None,
            "language_code": None,
            "latitude": i.get("latitude"), "longitude": i.get("longitude"),
            "altitude": None, "plus_code": None,
            "address_line_1": _address_line(i.get("address_parts")),
            "address_line_2": "",
            "postal_code": None,
            "country_code": i.get("country"),
            "geo_pcode": i.get("geo_pcode"),
        })

    households = []
    for h in hhs:
        members = by_hh.get(h["household_id"], [])
        head = next((m for m in members if m["individual_id"] == head_of.get(h["household_id"])), None)
        adults = [m for m in members if (m.get("age") or 0) >= 18]
        households.append({
            "internal_record_id": h["household_id"],
            "functional_record_id": h["household_id"],
            # Registries differ in what they store about a household; supplying
            # the union costs nothing, since each takes only the keys it asks for.
            "head_individual_id": h.get("head_individual_id"),
            "headship_type": h.get("headship_type"),
            "size_adults": len(adults),
            "size_elderly": sum(1 for m in members if (m.get("age") or 0) >= 60),
            "head_name": (head or {}).get("full_name") or "",
            "size_total": h.get("size_total") or len(members),
            "size_children_u5": 0, "size_school_age": 0,
            "number_of_female_members": sum(1 for m in members if m.get("gender") == "FEMALE"),
            "number_of_male_members": sum(1 for m in members if m.get("gender") == "MALE"),
            "latitude": h.get("latitude"), "longitude": h.get("longitude"),
            "altitude": None, "plus_code": None,
            "address_line_1": _address_line(h.get("address_parts")),
            "address_line_2": "",
            "postal_code": None,
            "country_code": h.get("country"),
            "geo_pcode": h.get("geo_pcode"),
        })

    print(f"[load-sample-data] master-data samples: {len(individuals)} individuals, "
          f"{len(households)} households (country={inds[0].get('country')}).")
    return individuals, households


# ── Attaching the registry's own sample rows to the loaded people ───────────
#
# The sub-table fixtures (land, crops, housing, programmes, vulnerability) link
# to the id space of the demography CSV — i0001, h001. Once people come from
# master-data those ids are ETH-IND-0001 and ETH-HH-001, and every one of those
# rows links to a record that does not exist. Nothing errors: the insert has no
# foreign key to violate, so they land as orphans and the registry comes up with
# farmers who own no land and households with no housing data.
#
# So the links are remapped onto whoever was actually loaded.

_REMAP_STATS = {}


def build_link_remap(individuals: list, households: list, fixture_rows: dict) -> dict:
    """old link id -> loaded record id.

    Distinct old ids are mapped in sorted order onto the loaded records, cycling
    when there are fewer people than the fixtures assume — the country pack
    carries a couple of dozen samples where the CSV carried five hundred, and
    dropping the surplus would empty most of the form.

    Person ids and household ids are mapped separately: a row linking to a
    household must not be handed a person.
    """
    ind_ids = [i["internal_record_id"] for i in individuals]
    hh_ids = [h["internal_record_id"] for h in households]
    if not ind_ids and not hh_ids:
        return {}

    # Ids the fixtures define themselves. A crop links to its parcel, and a
    # parcel is a fixture row, not a person — remapping that link would move the
    # crop onto a farmer and lose the parcel. Only links pointing OUT of the
    # fixture set name people or households.
    fixture_own_ids = {
        r["internal_record_id"]
        for rows in fixture_rows.values()
        for r in rows
        if r.get("internal_record_id")
    }

    old_person, old_household = set(), set()
    for rows in fixture_rows.values():
        for r in rows:
            link = r.get("link_internal_record_id")
            if not link or link in fixture_own_ids:
                continue
            # The fixtures' own convention, and the only signal available for
            # the rest: an id starting 'h' is a household, anything else a person.
            (old_household if str(link).startswith("h") else old_person).add(link)

    # An id that already names a loaded record maps to itself. That makes this a
    # strict no-op on the CSV path, where the fixtures and the people share an id
    # space — rather than relying on the two happening to be in the same order.
    loaded = set(ind_ids) | set(hh_ids)
    remap = {}
    for old_set, new_ids in ((sorted(old_person), ind_ids), (sorted(old_household), hh_ids)):
        if not new_ids:
            continue
        unmatched = [o for o in old_set if o not in loaded]
        for old in old_set:
            if old in loaded:
                remap[old] = old
        for index, old in enumerate(unmatched):
            remap[old] = new_ids[index % len(new_ids)]
    return remap


def remap_links(table: str, rows: list, remap: dict) -> list:
    """Repoint a fixture's links, and collapse it to one row per record when it
    was one row per record to begin with.

    Cycling turns 500 links into 21, so a table carrying exactly one row per
    person — housing, vulnerability — would otherwise give each of them a
    couple of dozen. Whether a table is one-per-record is read from the fixture
    rather than configured: if every original link appeared once, it is.
    """
    if not remap:
        return rows
    links = [r.get("link_internal_record_id") for r in rows if r.get("link_internal_record_id")]
    one_per_record = links and len(set(links)) == len(links)

    out, seen, unresolved = [], set(), 0
    for r in rows:
        link = r.get("link_internal_record_id")
        if link in remap:
            r = dict(r, link_internal_record_id=remap[link])
            if one_per_record:
                if r["link_internal_record_id"] in seen:
                    continue
                seen.add(r["link_internal_record_id"])
        elif link:
            # Points at another sub-table row rather than a person — a crop's
            # parcel. Those ids are internal to the fixture and stay valid.
            unresolved += 1
        out.append(r)

    _REMAP_STATS[table] = (len(rows), len(out), unresolved)
    return out


def report_link_remap() -> None:
    if not _REMAP_STATS:
        return
    for table, (before, after, unresolved) in sorted(_REMAP_STATS.items()):
        note = f"{table}: {before} fixture row(s) -> {after} attached"
        if before != after:
            note += " (one row per record; surplus dropped)"
        if unresolved:
            note += f", {unresolved} linked within the fixture"
        print(f"[load-sample-data]   {note}")


def report_geo_resolution() -> None:
    resolved, fallback = _GEO_STATS["resolved"], _GEO_STATS["fallback"]
    if not (resolved or fallback):
        return
    print(f"[load-sample-data] geo ids: {resolved} resolved against master-data, "
          f"{fallback} fell back to slug-paths.")
    if fallback:
        # Never silent: a fallback id joins to nothing when master-data was
        # seeded from a pack, and the only symptom is an empty map.
        print("[load-sample-data]   unresolved name chains, e.g. "
              + "; ".join(_GEO_STATS["unresolved_examples"]))
        print("[load-sample-data]   those records will not join to a boundary. "
              "Check the sample data's place names match the loaded country pack.")


def _read_csv_rows(path: Path, json_columns: set[str]) -> list[dict]:
    if not path.is_file():
        print(f"[load-sample-data] Missing file: {path}", file=sys.stderr)
        sys.exit(1)
    with path.open(newline="", encoding="utf-8") as f:
        out = []
        for row in csv.DictReader(f):
            parsed = {}
            for k, v in row.items():
                if v == "":
                    parsed[k] = None
                elif k in json_columns:
                    parsed[k] = json.loads(v)
                else:
                    parsed[k] = v
            out.append(parsed)
        return out



def _age_fields(i: dict) -> dict:
    """birth_date XOR estimated_age, with the matching age_method."""
    if i.get("birth_date"):
        return {"birth_date": i["birth_date"], "estimated_age": None, "age_method": "DOCUMENTED"}
    age = i.get("age")
    if age is None and i.get("birth_year"):
        age = date.today().year - int(i["birth_year"])
    return {
        "birth_date": None,
        "estimated_age": age,
        "age_method": "ESTIMATED" if age is not None else None,
    }

def _as_int(v):
    return int(v) if v not in (None, "") else None


def search_text_individual(ind: dict) -> str:
    parts = [
        ind["functional_record_id"],
        ind["full_name"],
        ind.get("foundational_id") or "",
        ind.get("foundational_id_masked") or "",
        ind.get("gender") or "",
        ind.get("birth_date") or "",
        str(ind.get("estimated_age") or ""),
        ind.get("marital_status") or "",
    ]
    return " ".join(p for p in parts if p)


def search_text_household(hh: dict) -> str:
    parts = [
        hh["functional_record_id"],
        hh["head_name"],
        hh["headship_type"],
        str(hh["size_total"]),
    ]
    return " ".join(p for p in parts if p)


def insert_individuals(cur, individuals: list[dict]) -> None:
    columns = [
        "internal_record_id", "functional_record_id",
        "link_internal_record_id", "link_foundational_id",
        "record_name", "record_image_document_id",
        "created_by", "created_at", "last_approved_at", "last_approved_by",
        "search_text", "record_status", "record_status_reason",
        "foundational_id", "first_name", "middle_name", "last_name",
        "given_name", "prefix", "suffix",
        "gender", "birth_date", "phone_numbers", "emails",
        "marital_status", "occupation", "income_level",
        "language_code", "education_level", "registration_date",
        "latitude", "longitude", "altitude", "plus_code",
        "address_line_1", "address_line_2", "postal_code", "country_code",
        "geo_lowest_level_value_id", "geo_code_hierarchy_json",
        "foundational_id_masked", "foundational_id_verification_status",
        "full_name", "estimated_age", "age_method",
    ]
    rows = []
    for ind in individuals:
        rows.append(
            (
                ind["internal_record_id"],
                ind["functional_record_id"],
                ind.get("household_id"),  # link to master Household register
                None,
                ind["full_name"],
                None,
                SEEDER,
                CREATED_AT,
                CREATED_AT,
                SEEDER,
                search_text_individual(ind),
                "ACTIVE",
                None,
                ind.get("foundational_id"),
                ind["first_name"],
                ind.get("middle_name"),
                ind["last_name"],
                ind["given_name"],
                None,
                None,
                ind["gender"],
                ind["birth_date"],
                to_json(ind.get("phone_numbers")),
                to_json([ind["emails"]] if ind.get("emails") else None),
                ind["marital_status"],
                None,
                None,
                ind.get("language_code"),
                ind.get("education_level"),
                "2026-04-01",
                ind["latitude"],
                ind["longitude"],
                ind["altitude"],
                ind["plus_code"],
                ind["address_line_1"],
                ind["address_line_2"],
                ind["postal_code"],
                ind["country_code"],
                geo_lowest_id(ind),
                geo_hierarchy(ind),
                ind["foundational_id_masked"],
                "VERIFIED",
                ind["full_name"],
                _as_int(ind.get("estimated_age")),
                ind["age_method"],
            )
        )
    sql = (
        f'INSERT INTO "public"."g2p_register_individuals" ('
        + ", ".join(f'"{c}"' for c in columns)
        + ") VALUES %s ON CONFLICT (\"internal_record_id\") DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows, template=None, page_size=200)
    print(f"[load-sample-data]   -> g2p_register_individuals: {len(rows)}")


def insert_households(cur, households: list[dict]) -> None:
    columns = [
        "internal_record_id", "functional_record_id",
        "link_internal_record_id", "link_foundational_id",
        "record_name", "record_image_document_id",
        "created_by", "created_at", "last_approved_at", "last_approved_by",
        "search_text", "record_status", "record_status_reason",
        "latitude", "longitude", "altitude", "plus_code",
        "address_line_1", "address_line_2", "postal_code", "country_code",
        "geo_lowest_level_value_id", "geo_code_hierarchy_json",
        "household_head_internal_record_id", "household_head_name",
        "headship_type", "size_total", "size_adults", "size_children_u5",
        "size_school_age", "size_elderly",
        "number_of_female_members", "number_of_male_members",
        "elderly_member_present",
    ]
    rows = []
    for hh in households:
        size_elderly = _as_int(hh.get("size_elderly")) or 0
        rows.append(
            (
                hh["internal_record_id"],
                hh["functional_record_id"],
                None,
                None,
                f"{hh['head_name']} {hh['functional_record_id']}",
                None,
                SEEDER,
                CREATED_AT,
                CREATED_AT,
                SEEDER,
                search_text_household(hh),
                "ACTIVE",
                None,
                hh["latitude"],
                hh["longitude"],
                hh["altitude"],
                hh["plus_code"],
                hh["address_line_1"],
                hh["address_line_2"],
                hh["postal_code"],
                hh["country_code"],
                geo_lowest_id(hh),
                geo_hierarchy(hh),
                hh["head_individual_id"],
                hh["head_name"],
                hh["headship_type"],
                _as_int(hh.get("size_total")),
                _as_int(hh.get("size_adults")),
                _as_int(hh.get("size_children_u5")),
                _as_int(hh.get("size_school_age")),
                size_elderly,
                _as_int(hh.get("number_of_female_members")),
                _as_int(hh.get("number_of_male_members")),
                "TRUE" if size_elderly > 0 else "FALSE",
            )
        )
    sql = (
        f'INSERT INTO "public"."g2p_register_households" ('
        + ", ".join(f'"{c}"' for c in columns)
        + ") VALUES %s ON CONFLICT (\"internal_record_id\") DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows, template=None, page_size=200)
    print(f"[load-sample-data]   -> g2p_register_households: {len(rows)}")


SUB_TABLES = [
    (
        "g2p_register_individual_livelihoods",
        "individual_livelihoods.json",
        ["primary_livelihood", "secondary_livelihood", "employment_status", "coping_strategies_index", "mobile_phone_type"],
    ),
    (
        "g2p_register_individual_livestock",
        "individual_livestock.json",
        ["livestock_species", "livestock_counts"],
    ),
    (
        "g2p_register_individual_land",
        "individual_land.json",
        ["land_access", "land_size", "productive_assets"],
    ),
    (
        "g2p_register_individual_shocks",
        "individual_shocks.json",
        ["shock_type", "shock_date", "shock_period", "coping_strategy"],
    ),
    (
        "g2p_register_individual_disabilities",
        "individual_disabilities.json",
        ["disability_domain", "disability_severity"],
    ),
    (
        "g2p_register_individual_vulnerability",
        "individual_vulnerability.json",
        [
            "disability_status", "orphanhood_flag", "chronic_illness_flag",
            "displacement_status", "pastoralist_classification",
            "high_mobility_indicator", "plw_status", "plw_status_date",
        ],
    ),
    (
        "g2p_register_individual_programs",
        "individual_programs.json",
        ["program_name", "program_start_date", "program_exit_date"],
    ),
    (
        "g2p_register_household_assets",
        "household_assets.json",
        ["asset_type", "asset_category", "quantity", "size_value", "size_unit", "size_band", "details"],
    ),
    (
        "g2p_register_household_housing_and_services",
        "household_housing_and_services.json",
        [
            "dwelling_type", "roof_material", "wall_material", "floor_material",
            "tenure_status", "water_source_type", "water_distance_minutes",
            "sanitation_type", "lighting_source", "cooking_fuel_type",
        ],
    ),
    (
        "g2p_register_household_programs",
        "household_programs.json",
        ["program_name", "program_start_date", "program_exit_date"],
    ),
]

COMMON_COLUMNS = [
    "internal_record_id", "functional_record_id",
    "link_internal_record_id", "link_foundational_id",
    "record_name", "record_image_document_id",
    "created_by", "created_at", "last_approved_at", "last_approved_by",
    "search_text", "record_status", "record_status_reason",
]


def insert_sub_table(cur, table: str, rows_json: list[dict], extra_cols: list[str]) -> None:
    if not rows_json:
        print(f"[load-sample-data]   -> {table}: 0 (empty)")
        return
    columns = COMMON_COLUMNS + extra_cols
    rows = []
    for r in rows_json:
        common = [
            r["internal_record_id"],
            r["functional_record_id"],
            r["link_internal_record_id"],
            r.get("link_foundational_id"),
            r["record_name"],
            r.get("record_image_document_id"),
            r.get("created_by", SEEDER),
            r.get("created_at", CREATED_AT),
            r.get("last_approved_at", CREATED_AT),
            r.get("last_approved_by", SEEDER),
            r["search_text"],
            r.get("record_status", "ACTIVE"),
            r.get("record_status_reason"),
        ]
        extras = [r.get(c) for c in extra_cols]
        rows.append(tuple(common + extras))

    sql = (
        f'INSERT INTO "public"."{table}" ('
        + ", ".join(f'"{c}"' for c in columns)
        + ") VALUES %s ON CONFLICT (\"internal_record_id\") DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows, template=None, page_size=200)
    print(f"[load-sample-data]   -> {table}: {len(rows)}")


def insert_scores(cur, scores: list[dict]) -> None:
    if not scores:
        return
    columns = [
        "internal_record_id", "register_id", "score_type", "score_definition_id",
        "link_internal_record_id", "triggered_by_cr_id", "triggered_by_submission_id",
        "computed_score", "computed_at",
    ]
    rows = [tuple(r.get(c) for c in columns) for r in scores]
    sql = (
        f'INSERT INTO "public"."g2p_register_scores" ('
        + ", ".join(f'"{c}"' for c in columns)
        + ") VALUES %s ON CONFLICT (\"internal_record_id\") DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows, template=None, page_size=200)
    print(f"[load-sample-data]   -> g2p_register_scores: {len(rows)}")


# Stable namespace so re-running the seed produces the same queue_id per
# (register, record, section) — combined with ON CONFLICT DO NOTHING this
# makes completion-score enqueueing idempotent.
_QUEUE_NS = uuid.UUID("a1b2c3d4-0000-4000-8000-000000000001")


def get_register_id(cur, mnemonic: str):
    cur.execute(
        'SELECT register_id FROM "public"."g2p_register_definitions" '
        "WHERE register_mnemonic = %s",
        (mnemonic,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def qualifying_sections(cur, register_id: str) -> list[str]:
    """Sections enqueued for completion scoring: own-register sections plus any
    list section, EXCLUDING sections backed by a CORE_TABLE register (e.g. the
    Score section).

    The completion-score worker resolves each section's model as
    G2PRegister<section_register_mnemonic> from the extensions
    register_domain.models. CORE_TABLE registers (e.g. Score) have no such
    generated model — their model lives in registry-core — so enqueuing them
    makes the worker fail with "has no attribute 'G2PRegisterScore'"."""
    cur.execute(
        "SELECT s.section_id, s.section_register_id, s.is_list, d.register_purpose "
        'FROM "public"."g2p_register_sections" s '
        'LEFT JOIN "public"."g2p_register_definitions" d '
        "  ON d.register_id = s.section_register_id "
        "WHERE s.register_id = %s",
        (register_id,),
    )
    out = []
    for section_id, section_register_id, is_list, purpose in cur.fetchall():
        if section_register_id != register_id and not is_list:
            continue
        if purpose == "CORE_TABLE":
            continue
        out.append(section_id)
    return out


def enqueue_completion_scores(cur, register_id: str, record_ids: list[str]) -> None:
    """Seed PENDING g2p_completion_score_computation_queue rows for each
    (record, qualifying section) so the worker computes scores later."""
    if not register_id:
        print("[load-sample-data]   -> completion-score queue: register not found, skipped")
        return
    sections = qualifying_sections(cur, register_id)
    if not sections:
        print(f"[load-sample-data]   -> completion-score queue ({register_id}): no sections")
        return
    rows = []
    for rid in record_ids:
        for sid in sections:
            queue_id = str(uuid.uuid5(_QUEUE_NS, f"{register_id}:{rid}:{sid}"))
            rows.append((queue_id, register_id, rid, sid, None, None, "PENDING", 0))
    columns = [
        "queue_id", "register_id", "internal_record_id", "section_id",
        "change_request_id", "submission_id",
        "compute_status", "compute_number_of_attempts",
    ]
    sql = (
        'INSERT INTO "public"."g2p_completion_score_computation_queue" ('
        + ", ".join(f'"{c}"' for c in columns)
        + ") VALUES %s ON CONFLICT (queue_id) DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows, template=None, page_size=500)
    print(
        f"[load-sample-data]   -> completion-score queue: {len(rows)} rows "
        f"({len(record_ids)} records x {len(sections)} sections)"
    )


def main() -> None:
    print("[load-sample-data] Starting…")
    print(f"[load-sample-data] OPENG2P_DATA_DIR = {OPENG2P_DATA_DIR}")
    print(f"[load-sample-data] NSR_SEED_DATA_DIR = {NSR_DATA_DIR}")

    # Before anything derives a geo id. Read once; every record resolves against
    # this rather than reopening master-data per row.
    global _GEO_INDEX, _GEO_BY_ID
    units = load_geo_units()
    _GEO_INDEX = load_geo_index(units)
    _GEO_BY_ID = load_geo_chain_by_id(units)

    # People come from master-data when it carries the country's samples. The
    # CSV is the fallback, and it can only ever describe the one country whose
    # five level names its columns happen to be.
    individuals, households = load_people_from_mds()
    if not individuals:
        print("[load-sample-data] no samples in master-data — falling back to the "
              "demography CSV. Enable geoSeed.load.samples for a pack-coherent set.")
        individuals = _read_csv_rows(DEMO_DIR / "individuals.csv", JSON_COLUMNS_INDIVIDUAL)
        households = _read_csv_rows(DEMO_DIR / "households.csv", JSON_COLUMNS_HOUSEHOLD)

    conn = psycopg2.connect(
        host=env("PGHOST"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=env("PGDATABASE"),
        user=env("PGUSER"),
        password=env("PGPASSWORD"),
    )
    conn.autocommit = False
    cur = conn.cursor()

    # Read every fixture first: the remap has to see all the links before it can
    # assign them, or two tables referring to the same person would disagree.
    fixtures = {fname: load_json(NSR_DATA_DIR / fname) for _, fname, _ in SUB_TABLES}
    fixtures["scores.json"] = load_json(NSR_DATA_DIR / "scores.json")
    remap = build_link_remap(individuals, households, fixtures)
    if remap:
        print(f"[load-sample-data] attaching fixture rows to {len(set(remap.values()))} "
              f"loaded record(s) ({len(remap)} fixture id(s) remapped):")

    try:
        insert_individuals(cur, individuals)
        insert_households(cur, households)
        for table, fname, extras in SUB_TABLES:
            rows = remap_links(table, fixtures[fname], remap)
            insert_sub_table(cur, table, rows, extras)
        insert_scores(cur, remap_links("g2p_register_scores", fixtures["scores.json"], remap))

        # Seed completion-score computation queue so the worker can compute
        # section completion scores for every seeded individual and household.
        enqueue_completion_scores(
            cur,
            get_register_id(cur, "Individual"),
            [ind["internal_record_id"] for ind in individuals],
        )
        enqueue_completion_scores(
            cur,
            get_register_id(cur, "Household"),
            [hh["internal_record_id"] for hh in households],
        )

        conn.commit()
        report_link_remap()
        report_geo_resolution()
        print("[load-sample-data] Done.")
    except Exception as exc:
        conn.rollback()
        print(f"[load-sample-data] FAILED: {exc}", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
