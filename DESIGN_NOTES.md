# Design Notes

## B2 — idempotency key

State exactly what key your `cost_tag_check.py` uses to decide whether two resources in the
same run are "the same" for dedup purposes, and why running it twice against an unchanged
plan file produces identical output and exit code without the script keeping any record
between runs. Use the word "idempotency" in your explanation.

Idempotency key: the resource address (e.g. aws_s3_bucket.listing_media,
aws_s3_bucket.landlord_media[0]). It's unique for every resource in a plan.
Failures are stored by address, so a resource listed twice is reported once. They're
printed sorted, so the order never changes, and the exit code depends only on whether
anything failed. Nothing is saved between runs, so the output depends only on the plan
file. That gives idempotency: running it again on the same plan gives exactly the same
output and exit code (see TERMINAL_LOG.md).

Rejected keys:

- type + name: would merge landlord_media[0] and [1].

- bucket name or function name: only works for some resource types.

- a hash of the tags: changes whenever the tags change.

## Any other decision with a non-obvious alternative

- B0: for_each + moved (chosen) vs. for_each alone (would recreate all 4) vs.
terraform state mv (manual, not reviewed).

- B0: the prevent_destroy lock (chosen) vs. relying on people reading plans.

- B1: Intelligent-Tiering + tag filter (chosen) vs. Glacier later (only reduces the
problem).

- B2: replaces are checked (chosen) vs. skipped (untagged resources would slip through).

- B2: follow the chain at check time (chosen) vs. copying landlord_account_id onto
tenants and reports (models can't change, and the copies could get out of sync).
