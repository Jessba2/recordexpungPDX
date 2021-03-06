import unittest

from datetime import date
from dateutil.relativedelta import relativedelta
from expungeservice.models.disposition import Disposition
from tests.factories.charge_factory import ChargeFactory
from tests.factories.case_factory import CaseFactory


class TestChargeClass(unittest.TestCase):

    TEN_YEARS_AGO = date.today() + relativedelta(years=-10)
    LESS_THAN_TEN_YEARS_AGO = date.today() + relativedelta(years=-10, days=+1)
    LESS_THAN_THREE_YEARS_AGO = date.today() + relativedelta(years=-3, days=+1)
    THREE_YEARS_AGO = date.today() + relativedelta(years=-3)

    def setUp(self):
        self.charge = ChargeFactory.build()

    def test_it_initializes_simple_statute(self):
        self.charge["statute"] = "1231235B"
        charge = ChargeFactory.save(self.charge)

        assert charge.statute == "1231235B"

    def test_it_normalizes_statute(self):
        self.charge["statute"] = "-123.123(5)()B"
        charge = ChargeFactory.save(self.charge)

        assert charge.statute == "1231235B"

    def test_it_converts_statute_to_uppercase(self):
        self.charge["statute"] = "-123.123(5)()b"
        charge = ChargeFactory.save(self.charge)

        assert charge.statute == "1231235B"

    def test_it_retrieves_its_parent_instance(self):
        case = CaseFactory.create()
        charge = ChargeFactory.create(case=case)

        assert charge.case()() is case

    def test_it_knows_if_it_has_a_recent_conviction_happy_path(self):
        charge = ChargeFactory.create()
        charge.disposition = Disposition(self.LESS_THAN_TEN_YEARS_AGO, "Convicted")

        assert charge.recent_conviction() is True

    def test_it_knows_if_it_has_a_recent_conviction_sad_path(self):
        charge = ChargeFactory.create()
        charge.disposition = Disposition(self.TEN_YEARS_AGO, "Convicted")

        assert charge.recent_conviction() is False

    def test_dismissed_charge_is_not_a_recent_conviction(self):
        charge = ChargeFactory.create()
        charge.disposition = Disposition(self.LESS_THAN_TEN_YEARS_AGO, "Dismissed")

        assert charge.recent_conviction() is False

    def test_most_recent_acquittal_happy_path(self):
        charge = ChargeFactory.create(date=self.LESS_THAN_THREE_YEARS_AGO)
        charge.disposition = Disposition(date=self.LESS_THAN_THREE_YEARS_AGO, ruling="Dismissed")

        assert charge.recent_acquittal() is True

    def test_most_recent_acquittal_sad_path(self):
        charge = ChargeFactory.create(date=self.THREE_YEARS_AGO)
        charge.disposition = Disposition(date=self.THREE_YEARS_AGO, ruling="Dismissed")

        assert charge.recent_acquittal() is False

    def test_convicted_charge_is_not_a_recent_acquittal(self):
        charge = ChargeFactory.create(date=self.LESS_THAN_THREE_YEARS_AGO)
        charge.disposition = Disposition(date=self.LESS_THAN_THREE_YEARS_AGO, ruling="Convicted")

        assert charge.recent_acquittal() is False

    def test_same_charge_is_not_equal(self):
        case = CaseFactory.create(case_number="C0000")
        mrc_charge = ChargeFactory.create(case=case)
        second_mrc_charge = ChargeFactory.create(case=case)

        assert mrc_charge != second_mrc_charge


class TestChargeStatuteSectionAssignment(unittest.TestCase):
    def test_it_sets_section_to_the_first_6_digits_of_statute(self):
        charge = ChargeFactory.create(statute="1231235B")

        assert charge._section == "123123"

    def test_it_sets_section_to_the_first_7_digits_when_4th_char_in_statute_is_a_letter(self):
        charge = ChargeFactory.create(statute="475B3493C")

        assert charge._section == "475B349"

    def test_it_sets_section_to_none_if_statute_is_does_not_contain_a_section(self):
        charge = ChargeFactory.create(statute="29")

        assert charge._section == ""

    def test_it_normalizes_section(self):
        charge = ChargeFactory.create(statute="475B.349(3)(C)")

        assert charge._section == "475B349"
