"""M05.2 — backups, Multi-AZ and protection from deletion, for prod and for lab."""
import pytest


def database(resources, env):
    res = resources("data", Env=env)
    assert res.get("Database", {}).get("Type") == "AWS::RDS::DBInstance", "add Database (AWS::RDS::DBInstance) to infra/data.yaml"
    return res["Database"]["Properties"]


@pytest.mark.parametrize("env,expected", [("prod", True), ("lab", False)])
def test_multi_az_only_in_prod(resources, env, expected):
    value = database(resources, env).get("MultiAZ")
    assert value is expected, \
        f"{env}: MultiAZ is {value!r}; use !If [IsProd, true, false]. Multi-AZ keeps a synchronous standby in another zone and fails over by itself ({'prod needs it' if expected else 'lab does not need to pay twice for the instance'})"


@pytest.mark.parametrize("env,minimum", [("prod", 7), ("lab", 1)])
def test_automated_backups_are_on(resources, env, minimum):
    days = database(resources, env).get("BackupRetentionPeriod")
    assert isinstance(days, int) and days >= minimum, \
        f"{env}: BackupRetentionPeriod is {days!r}; use at least {minimum} (prod 7, lab 1). 0 switches automated backups off, and with them point-in-time recovery"
    assert days <= 35, f"{env}: BackupRetentionPeriod {days} is above the 35-day maximum"


@pytest.mark.parametrize("env,expected", [("prod", True), ("lab", False)])
def test_deletion_protection_only_in_prod(resources, env, expected):
    value = database(resources, env).get("DeletionProtection")
    assert value is expected, \
        f"{env}: DeletionProtection is {value!r}; use !If [IsProd, true, false]. In prod nobody can delete the database (even by deleting the stack) until the flag is switched off first; lab stays disposable"


@pytest.mark.parametrize("env", ["prod", "lab"])
def test_tags_are_copied_to_snapshots(resources, env):
    assert database(resources, env).get("CopyTagsToSnapshot") is True, \
        f"{env}: set CopyTagsToSnapshot: true so every snapshot carries the project and env tags (cost reports and tag-based IAM keep working)"


def test_deleting_the_stack_takes_a_snapshot(template):
    res = template("data")["Resources"].get("Database", {})
    assert res.get("DeletionPolicy") == "Snapshot", \
        "Database: add DeletionPolicy: Snapshot at the resource level (next to Type, not under Properties); deleting the stack then takes a final snapshot"
    assert res.get("UpdateReplacePolicy") == "Snapshot", \
        "Database: add UpdateReplacePolicy: Snapshot too; a change that replaces the instance then snapshots the old one instead of deleting it"
