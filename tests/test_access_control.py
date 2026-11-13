"""
Tests for can_access_screening_report().

The access boundary is the LandlordAccount: a PropertyManager may view a ScreeningReport only
if report -> tenant -> property -> landlord_account_id matches their own. Missing links in that
chain must fail closed.
"""
import pytest

from app.access_control import can_access_screening_report
from app.models import ScreeningReport, Tenant


def _by_id(records, record_id):
    return next(r for r in records if r.id == record_id)


def test_pm_001_can_access_own_account_report(
    property_managers, properties, tenants, screening_reports
):
    pm = _by_id(property_managers, "pm-001")
    report = _by_id(screening_reports, "rep-001")

    assert can_access_screening_report(
        pm, report, properties=properties, tenants=tenants
    ) is True


def test_pm_001_denied_other_account_report(
    property_managers, properties, tenants, screening_reports
):
    pm = _by_id(property_managers, "pm-001")
    report = _by_id(screening_reports, "rep-002")

    assert can_access_screening_report(
        pm, report, properties=properties, tenants=tenants
    ) is False


def test_pm_002_denied_other_account_report(
    property_managers, properties, tenants, screening_reports
):
    pm = _by_id(property_managers, "pm-002")
    report = _by_id(screening_reports, "rep-001")

    assert can_access_screening_report(
        pm, report, properties=properties, tenants=tenants
    ) is False


@pytest.mark.parametrize("pm_id", ["pm-001", "pm-002"])
def test_report_with_unknown_tenant_is_denied(
    pm_id, property_managers, properties, tenants
):
    pm = _by_id(property_managers, pm_id)
    orphan_report = ScreeningReport(
        id="rep-orphan", tenant_id="ten-does-not-exist", ssn_last4="0000", credit_score=700
    )

    assert can_access_screening_report(
        pm, orphan_report, properties=properties, tenants=tenants
    ) is False


@pytest.mark.parametrize("pm_id", ["pm-001", "pm-002"])
def test_tenant_with_unknown_property_is_denied(
    pm_id, property_managers, properties, tenants
):
    pm = _by_id(property_managers, pm_id)
    orphan_tenant = Tenant(id="ten-orphan", name="Nobody", property_id="prop-does-not-exist")
    report = ScreeningReport(
        id="rep-orphan", tenant_id=orphan_tenant.id, ssn_last4="0000", credit_score=700
    )

    assert can_access_screening_report(
        pm, report, properties=properties, tenants=[*tenants, orphan_tenant]
    ) is False
