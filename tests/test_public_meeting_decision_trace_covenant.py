import hashlib
import json
from pathlib import Path

import pytest


CONTRACT = str(
    Path(__file__).parents[1]
    / "contracts"
    / "public_meeting_decision_trace_covenant.py"
)
HOST = "records.example.gov"
AGENDA_URL = "https://records.example.gov/agenda"
MINUTES_URL = "https://records.example.gov/minutes"
RESOLUTION_URL = "https://records.example.gov/resolution"
ANNOUNCEMENT_URL = "https://records.example.gov/announcement"
HASH = "a" * 64
RECORD_BODY = "official public record"
RECORD_HASH = hashlib.sha256(RECORD_BODY.encode("utf-8")).hexdigest()


def _decision(status, mismatch=0, missing=0, vote="APPROVED"):
    return json.dumps(
        {
            "status": status,
            "mismatch_mask": mismatch,
            "missing_mask": missing,
            "vote_outcome": vote,
        }
    )


def _seed_sealed_case(contract):
    contract.create_meeting_case("meeting-1", HOST, "2026-04-14", RECORD_HASH)
    contract.add_artifact("meeting-1", 1, AGENDA_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 2, MINUTES_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 4, RESOLUTION_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 8, ANNOUNCEMENT_URL, RECORD_HASH)
    contract.seal_case("meeting-1")


def _mock_sources(vm):
    vm.strict_mocks = True
    for url in (AGENDA_URL, MINUTES_URL, RESOLUTION_URL, ANNOUNCEMENT_URL):
        vm.mock_web(url, {"status": 200, "body": RECORD_BODY})


def test_create_validates_owner_and_draft_replacement(
    direct_vm, direct_deploy, direct_bob
):
    contract = direct_deploy(CONTRACT)
    contract.create_meeting_case("meeting-1", HOST, "2026-04-14", HASH)
    contract.add_artifact("meeting-1", 1, AGENDA_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 1, "https://records.example.gov/agenda-v2", RECORD_HASH)
    with direct_vm.prank(direct_bob), direct_vm.expect_revert("UNAUTHORIZED"):
        contract.add_artifact("meeting-1", 2, MINUTES_URL, RECORD_HASH)
    with direct_vm.expect_revert("INVALID_ARTIFACT_URL"):
        contract.add_artifact("meeting-1", 2, "http://records.example.gov/minutes", RECORD_HASH)


def test_seal_requires_core_records_and_locks_artifacts(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    contract.create_meeting_case("meeting-1", HOST, "2026-04-14", HASH)
    contract.add_artifact("meeting-1", 1, AGENDA_URL, RECORD_HASH)
    with direct_vm.expect_revert("MISSING_ESSENTIAL_ARTIFACT"):
        contract.seal_case("meeting-1")
    contract.add_artifact("meeting-1", 2, MINUTES_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 4, RESOLUTION_URL, RECORD_HASH)
    contract.seal_case("meeting-1")
    with direct_vm.expect_revert("ARTIFACTS_LOCKED"):
        contract.add_artifact("meeting-1", 8, ANNOUNCEMENT_URL, RECORD_HASH)


def test_supported_result_and_exact_validator_binding(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    _mock_sources(direct_vm)
    direct_vm.mock_llm("public meeting decision trace", _decision("SUPPORTED"))
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1") == ("SUPPORTED", 0, 0, "APPROVED", 1)
    assert direct_vm.run_validator() is True
    assert (
        direct_vm.run_validator(
            leader_result=_decision("SUPPORTED", mismatch=4, missing=0, vote="APPROVED")
        )
        is False
    )
    assert direct_vm.run_validator(leader_result=_decision("SUPPORTED", vote="DEFERRED")) is False


def test_agenda_commitment_mismatch_fails_closed(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    contract.create_meeting_case("meeting-1", HOST, "2026-04-14", HASH)
    contract.add_artifact("meeting-1", 1, AGENDA_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 2, MINUTES_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 4, RESOLUTION_URL, RECORD_HASH)
    contract.seal_case("meeting-1")
    direct_vm.mock_web(AGENDA_URL, {"status": 200, "body": RECORD_BODY})
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("UNRESOLVED", 0, 8, "UNKNOWN")
    assert direct_vm.run_validator() is True


def test_missing_optional_announcement_is_partial(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    contract.create_meeting_case("meeting-1", HOST, "2026-04-14", RECORD_HASH)
    contract.add_artifact("meeting-1", 1, AGENDA_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 2, MINUTES_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 4, RESOLUTION_URL, RECORD_HASH)
    contract.seal_case("meeting-1")
    direct_vm.strict_mocks = True
    for url in (AGENDA_URL, MINUTES_URL, RESOLUTION_URL):
        direct_vm.mock_web(url, {"status": 200, "body": RECORD_BODY})
    direct_vm.mock_llm(
        "public meeting decision trace", _decision("PARTIALLY_SUPPORTED", missing=8)
    )
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("PARTIALLY_SUPPORTED", 0, 8, "APPROVED")


@pytest.mark.parametrize(
    ("status", "mismatch", "vote"),
    [
        ("MATERIAL_MISMATCH", 1, "APPROVED"),
        ("MATERIAL_MISMATCH", 2, "APPROVED"),
        ("MATERIAL_MISMATCH", 4, "REJECTED"),
        ("MATERIAL_MISMATCH", 8, "DEFERRED"),
        ("MATERIAL_MISMATCH", 16, "NO_RECORDED_VOTE"),
    ],
)
def test_each_mismatch_bit_is_stored_and_bound(
    direct_vm, direct_deploy, status, mismatch, vote
):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    _mock_sources(direct_vm)
    direct_vm.mock_llm("public meeting decision trace", _decision(status, mismatch, 0, vote))
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == (status, mismatch, 0, vote)
    assert direct_vm.run_validator() is True


def test_transient_source_failure_is_unresolved(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    direct_vm.strict_mocks = True
    direct_vm.mock_web(AGENDA_URL, {"status": 500, "body": "temporary failure"})
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("UNRESOLVED", 0, 0, "UNKNOWN")
    assert direct_vm.run_validator() is True


def test_redirect_response_fails_closed(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    direct_vm.strict_mocks = True
    direct_vm.mock_web(AGENDA_URL, {"status": 302, "body": b"redirect"})
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("UNRESOLVED", 0, 0, "UNKNOWN")
    assert direct_vm.run_validator() is True


def test_hash_mismatch_fails_closed(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    direct_vm.strict_mocks = True
    direct_vm.mock_web(AGENDA_URL, {"status": 200, "body": "changed record"})
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("UNRESOLVED", 0, 0, "UNKNOWN")
    assert direct_vm.run_validator() is True


def test_malformed_model_output_fails_closed(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    _mock_sources(direct_vm)
    direct_vm.mock_llm("public meeting decision trace", "not-json")
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("UNRESOLVED", 0, 0, "UNKNOWN")
    assert direct_vm.run_validator() is True


def test_malformed_utf8_source_fails_closed(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    direct_vm.strict_mocks = True
    direct_vm.mock_web(AGENDA_URL, {"status": 200, "body": b"\xff\xfe"})
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("UNRESOLVED", 0, 0, "UNKNOWN")
    assert direct_vm.run_validator() is True


def test_missing_source_body_fails_closed(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    direct_vm.strict_mocks = True
    direct_vm.mock_web(AGENDA_URL, {"status": 200, "body": None})
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("UNRESOLVED", 0, 0, "UNKNOWN")
    assert direct_vm.run_validator() is True


def test_confirmed_missing_core_source_is_no_public_trace(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    direct_vm.strict_mocks = True
    direct_vm.mock_web(AGENDA_URL, {"status": 404, "body": "not found"})
    contract.assess_trace("meeting-1")
    assert contract.read_trace("meeting-1")[0:4] == ("NO_PUBLIC_TRACE", 0, 1, "UNKNOWN")
    assert direct_vm.run_validator() is True


def test_challenge_rejects_stale_revision_and_keeps_history(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    _seed_sealed_case(contract)
    _mock_sources(direct_vm)
    direct_vm.mock_llm("public meeting decision trace", _decision("SUPPORTED"))
    contract.assess_trace("meeting-1")
    first_manifest = contract.read_artifact_manifest_hash("meeting-1")
    with direct_vm.expect_revert("STALE_REVISION"):
        contract.challenge_trace("meeting-1", 0)
    contract.challenge_trace("meeting-1", 1)
    assert contract.read_trace("meeting-1")[0:4] == ("", 0, 0, "")
    assert contract.read_artifact_manifest_hash("meeting-1") == ""
    contract.add_artifact("meeting-1", 1, AGENDA_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 2, MINUTES_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 4, RESOLUTION_URL, RECORD_HASH)
    contract.add_artifact("meeting-1", 8, ANNOUNCEMENT_URL, RECORD_HASH)
    contract.seal_case("meeting-1")
    contract.resolve_challenge("meeting-1")
    assert contract.read_artifact_manifest_hash("meeting-1") != first_manifest
    assert contract.read_trace("meeting-1")[-1] == 2
    assert contract.read_history("meeting-1", 1) == ("SUPPORTED", 0, 0, "APPROVED")
