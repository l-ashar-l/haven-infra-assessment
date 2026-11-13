"""
B2, part 2 — implement the cost-tagging check.

Read fixtures/plan.json for the shape of a `terraform show -json` plan: a `resource_changes`
list, where each entry has a `type`, an `address`, and `change.after.tags`.

Implement check_plan() so it:
  - Looks at every resource being created or updated (skip anything whose change.actions
    isn't "create" or "update" — a "no-op"/"read" change, or a "delete" with no `after`
    block at all).
  - Fails (returns a non-zero exit code) if the resource is missing the tag that identifies
    the real billing unit, per README.md's domain model — not whatever tag the resource
    happens to already carry.
  - Is idempotent: running this twice against the same plan file produces the same result,
    with no duplicate output and no flipped pass/fail. This is about a single run being
    stable and repeatable — it does not require remembering anything between runs.
  - Prints which specific resource address(es) are missing the tag.

Run manually: python scripts/cost_tag_check.py fixtures/plan.json
"""
import json
import sys


REQUIRED_TAG = "landlord_account_id"
CHECKED_ACTIONS = {"create", "update"}


def _resources_missing_tag(plan: dict) -> list[str]:
    """Return the addresses of created/updated resources lacking REQUIRED_TAG, in plan order."""
    missing: list[str] = []
    seen: set[str] = set()

    for rc in plan.get("resource_changes", []):
        change = rc.get("change") or {}
        actions = set(change.get("actions") or [])
        if not actions & CHECKED_ACTIONS:
            continue

        after = change.get("after")
        if after is None:
            # Nothing will exist after apply, so there is nothing to tag.
            continue

        tags = after.get("tags") or {}
        if tags.get(REQUIRED_TAG):
            continue

        address = rc.get("address", "<unknown address>")
        if address not in seen:
            seen.add(address)
            missing.append(address)

    return missing


def check_plan(plan_path: str) -> int:
    """
    Returns an exit code: 0 if every resource being created or updated has
    `landlord_account_id`, non-zero otherwise.
    """
    with open(plan_path) as f:
        plan = json.load(f)

    missing = _resources_missing_tag(plan)
    if not missing:
        print(f"OK: all created/updated resources carry `{REQUIRED_TAG}`.")
        return 0

    print(f"FAIL: {len(missing)} resource(s) missing required tag `{REQUIRED_TAG}`:")
    for address in missing:
        print(f"  - {address}")
    return 1


if __name__ == "__main__":
    sys.exit(check_plan(sys.argv[1]))
