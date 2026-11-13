"""
Tests for scripts/cost_tag_check.py.

The check must flag created/updated resources missing `landlord_account_id` (the billing-unit
tag per README.md), ignore no-op and delete entries, and be stable across repeated runs.
"""
import json
from pathlib import Path

import pytest

from scripts.cost_tag_check import check_plan

FIXTURE_PLAN = Path(__file__).resolve().parent.parent / "fixtures" / "plan.json"

MISSING_TAG = [
    "aws_s3_bucket.listing_media",
    "aws_lambda_function.mls_feed_sync",
]
HAS_TAG = [
    "aws_s3_bucket.landlord_media[0]",
    "aws_lambda_function.screening_report_export",
]
SKIPPED = [
    "aws_s3_bucket.archive_media",  # no-op
    "aws_s3_bucket.decommissioned_media",  # delete, after is null
]


def _write_plan(tmp_path: Path, resource_changes: list[dict]) -> str:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"format_version": "1.2", "resource_changes": resource_changes}))
    return str(plan_path)


def test_fixture_plan_fails_and_flags_untagged_resources(capsys):
    exit_code = check_plan(str(FIXTURE_PLAN))
    out = capsys.readouterr().out

    assert exit_code != 0
    for address in MISSING_TAG:
        assert address in out
    for address in HAS_TAG + SKIPPED:
        assert address not in out


def test_fixture_plan_lists_each_missing_resource_exactly_once(capsys):
    check_plan(str(FIXTURE_PLAN))
    out = capsys.readouterr().out

    for address in MISSING_TAG:
        assert out.count(address) == 1


def test_running_twice_is_idempotent(capsys):
    first_code = check_plan(str(FIXTURE_PLAN))
    first_out = capsys.readouterr().out

    second_code = check_plan(str(FIXTURE_PLAN))
    second_out = capsys.readouterr().out

    assert first_code == second_code
    assert first_out == second_out
    for address in MISSING_TAG:
        assert second_out.count(address) == 1


def test_fully_tagged_plan_passes(tmp_path, capsys):
    plan_path = _write_plan(
        tmp_path,
        [
            {
                "address": "aws_s3_bucket.ok",
                "type": "aws_s3_bucket",
                "name": "ok",
                "change": {
                    "actions": ["create"],
                    "after": {"tags": {"landlord_account_id": "la-001"}},
                },
            }
        ],
    )

    assert check_plan(plan_path) == 0
    assert "aws_s3_bucket.ok" not in capsys.readouterr().out


def test_tenant_id_alone_is_not_sufficient(tmp_path, capsys):
    plan_path = _write_plan(
        tmp_path,
        [
            {
                "address": "aws_s3_bucket.tenant_tagged",
                "type": "aws_s3_bucket",
                "name": "tenant_tagged",
                "change": {
                    "actions": ["update"],
                    "after": {"tags": {"tenant_id": "ten-001"}},
                },
            }
        ],
    )

    assert check_plan(plan_path) != 0
    assert "aws_s3_bucket.tenant_tagged" in capsys.readouterr().out


@pytest.mark.parametrize(
    "change",
    [
        {"actions": ["no-op"], "after": {"tags": {}}},
        {"actions": ["read"], "after": {"tags": {}}},
        {"actions": ["delete"], "after": None},
        {"actions": ["delete"]},
    ],
)
def test_non_create_update_changes_are_ignored(tmp_path, capsys, change):
    plan_path = _write_plan(
        tmp_path,
        [{"address": "aws_s3_bucket.ignored", "type": "aws_s3_bucket", "name": "ignored", "change": change}],
    )

    assert check_plan(plan_path) == 0
    assert "aws_s3_bucket.ignored" not in capsys.readouterr().out


def test_repeated_untagged_address_is_printed_exactly_once(tmp_path, capsys):
    untagged = {
        "address": "aws_s3_bucket.repeated",
        "type": "aws_s3_bucket",
        "name": "repeated",
        "change": {"actions": ["create"], "after": {"tags": {}}},
    }
    plan_path = _write_plan(tmp_path, [untagged, dict(untagged)])

    exit_code = check_plan(plan_path)
    out = capsys.readouterr().out

    assert exit_code != 0
    assert out.count("aws_s3_bucket.repeated") == 1


def test_empty_plan_passes(tmp_path):
    assert check_plan(_write_plan(tmp_path, [])) == 0
