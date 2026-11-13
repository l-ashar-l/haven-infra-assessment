# Terminal log

## Starter repo
$ git log --oneline        (the d14c451 entry you already have)
$ git status
$ ls -la

## Setup
$ python3 --version
...
$ terraform version
...
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
...
$ cd terraform && terraform init -no-color && terraform validate -no-color && terraform plan -refresh=false -no-color; cd ..
...

## B2 test run 1: access check
$ python -m pytest tests/test_access_control.py -v
...
exit code: 0

## B2 test run 2: cost-tag check
$ python -m pytest tests/test_cost_tag_check.py -v
...
exit code: 0

## Cost-tag check, run 1
$ python scripts/cost_tag_check.py fixtures/plan.json
...

## Cost-tag check, run 2 (same input, same output = idempotent)
$ python scripts/cost_tag_check.py fixtures/plan.json
...
$ diff <(python scripts/cost_tag_check.py fixtures/plan.json) <(python scripts/cost_tag_check.py fixtures/plan.json) && echo "identical"
identical

## Final state
$ python -m pytest -v
...
$ git log --oneline
...
