"""Small checks for the places where a plausible-looking KPI could be wrong."""
import unittest

import pandas as pd

from pipeline.clean import duplicate_rows_for_review
from pipeline.metrics import build_definition_comparison
from pipeline.validate import (
    ValidationError, validate_timestamp_parsing, validate_dispatch_coverage,
    validate_journey, validate_ids,
)


class DataContractTests(unittest.TestCase):
    def test_conflicting_events_are_preserved_for_review(self):
        events = pd.DataFrame({"interaction_id": ["I1", "I1"], "order_id": ["O1", "O2"]})
        review = duplicate_rows_for_review(events, "interaction_id")
        self.assertEqual(set(review.order_id), {"O1", "O2"})
        self.assertEqual(review.retained_in_baseline.tolist(), [True, False])
        self.assertEqual(set(review.duplicate_kind), {"conflicting_id"})

    def test_exact_copies_are_not_labelled_conflicts(self):
        events = pd.DataFrame({"interaction_id": ["I1", "I1"], "order_id": ["O1", "O1"]})
        self.assertEqual(set(duplicate_rows_for_review(events, "interaction_id").duplicate_kind), {"exact_duplicate"})

    def test_bad_timestamp_fails_but_missing_is_handled_separately(self):
        validate_timestamp_parsing(pd.DataFrame({"time": [None]}), ["time"], "orders")
        with self.assertRaises(ValidationError):
            validate_timestamp_parsing(pd.DataFrame({"time": ["not-a-date"]}), ["time"], "orders")

    def test_missing_ids_fail(self):
        for value in [None, "  "]:
            with self.assertRaises(ValidationError):
                validate_ids(pd.DataFrame({"order_id": [value]}), ["order_id"], "orders")

    def test_dispatch_must_cover_each_order_once(self):
        orders = pd.DataFrame({"order_id": ["O1", "O2"]})
        for ids in [["O1"], ["O1", "O1", "O2"]]:
            with self.assertRaises(ValidationError):
                validate_dispatch_coverage(orders, pd.DataFrame({"order_id": ids}))

    def test_join_fanout_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_journey(pd.DataFrame({"order_id": ["O1", "O1"]}), 1)

    def test_threshold_boundary_and_missing_promise(self):
        journey = pd.DataFrame({
            "kpi_eligible": [True, True, True, False],
            "final_status": ["delivered"] * 4,
            "actual_delivery_at": pd.to_datetime(["2026-08-01"] * 4),
            "promised_eta": pd.to_datetime(["2026-08-01"] * 3 + [None]),
            "delay_min": [0, 10, 11, float("nan")],
        })
        rows = build_definition_comparison(journey)
        self.assertEqual(rows.iloc[0].late_orders, 2)
        self.assertEqual(rows.iloc[1].late_orders, 1)
        self.assertEqual(rows.iloc[2].unclassifiable_orders, 1)
        self.assertTrue(pd.isna(rows.iloc[2].late_rate_pct))


if __name__ == "__main__":
    unittest.main()
