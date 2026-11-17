from Versions.PriceLevelBook import PriceLevelBook
import unittest


class TestOrderBook(unittest.TestCase):

    def setUp(self):
        self.ob = PriceLevelBook()

    def test_buy_added_to_book(self):

        self.assertEqual(
            self.ob.add_limit(1, "B", 100, 10),
            []
        )

        self.assertEqual(self.ob.best_bid(), 100)

    def test_sell_added_to_book(self):

        self.assertEqual(
            self.ob.add_limit(1, "S", 100, 10),
            []
        )

        self.assertEqual(self.ob.best_ask(), 100)

    def test_no_match(self):

        self.ob.add_limit(1, "S", 105, 10)

        self.assertEqual(
            self.ob.add_limit(2, "B", 100, 10),
            []
        )

        self.assertEqual(self.ob.best_ask(), 105)
        self.assertEqual(self.ob.best_bid(), 100)

    def test_exact_fill(self):

        self.ob.add_limit(1, "S", 100, 10)

        self.assertEqual(
            self.ob.add_limit(2, "B", 100, 10),
            [(2, 1, 100, 10)]
        )

        with self.assertRaises(IndexError):
            self.ob.best_ask()

        with self.assertRaises(IndexError):
            self.ob.best_bid()

    def test_partial_fill_resting_survives(self):

        self.ob.add_limit(1, "S", 100, 20)

        self.assertEqual(
            self.ob.add_limit(2, "B", 100, 5),
            [(2, 1, 100, 5)]
        )

        self.assertEqual(self.ob.best_ask(), 100)

        self.assertEqual(
            self.ob.add_limit(3, "B", 100, 50),
            [(3, 1, 100, 15)]
        )

    def test_partial_fill_incoming_survives(self):

        self.ob.add_limit(1, "S", 100, 5)

        self.assertEqual(
            self.ob.add_limit(2, "B", 100, 20),
            [(2, 1, 100, 5)]
        )

        self.assertEqual(self.ob.best_bid(), 100)

        with self.assertRaises(IndexError):
            self.ob.best_ask()

        self.assertEqual(
            self.ob.add_limit(3, "S", 100, 50),
            [(2, 3, 100, 15)]
        )

    def test_multiple_matches(self):

        self.ob.add_limit(1, "S", 100, 3)
        self.ob.add_limit(2, "S", 101, 4)
        self.ob.add_limit(3, "S", 102, 5)

        self.assertEqual(
            self.ob.add_limit(4, "B", 102, 10),
            [(4, 1, 100, 3), (4, 2, 101, 4), (4, 3, 102, 3)]
        )

        self.assertEqual(self.ob.best_ask(), 102)

        self.assertEqual(
            self.ob.add_limit(5, "B", 102, 50),
            [(5, 3, 102, 2)]
        )

    def test_price_priority(self):

        self.ob.add_limit(1, "B", 100, 5)
        self.ob.add_limit(2, "B", 105, 5)

        self.assertEqual(
            self.ob.add_limit(3, "S", 90, 5),
            [(2, 3, 105, 5)]
        )

        self.assertEqual(self.ob.best_bid(), 100)

    def test_time_priority_same_price(self):

        self.ob.add_limit(1, "B", 100, 5)
        self.ob.add_limit(2, "B", 100, 5)

        self.assertEqual(
            self.ob.add_limit(3, "S", 100, 7),
            [(1, 3, 100, 5), (2, 3, 100, 2)]
        )

        self.assertEqual(
            self.ob.add_limit(4, "S", 100, 50),
            [(2, 4, 100, 3)]
        )

    def test_multiple_orders_same_price_fifo(self):

        self.ob.add_limit(1, "S", 100, 2)
        self.ob.add_limit(2, "S", 100, 2)
        self.ob.add_limit(3, "S", 100, 2)

        self.assertEqual(
            self.ob.add_limit(4, "B", 100, 5),
            [(4, 1, 100, 2), (4, 2, 100, 2), (4, 3, 100, 1)]
        )

        self.assertEqual(
            self.ob.add_limit(5, "B", 100, 50),
            [(5, 3, 100, 1)]
        )

    def test_fill_price_is_resting_price(self):

        self.ob.add_limit(1, "S", 100, 5)

        self.assertEqual(
            self.ob.add_limit(2, "B", 110, 5),
            [(2, 1, 100, 5)]
        )

    # ---------- cancel ----------

    def test_cancel_existing_order(self):

        self.ob.add_limit(1, "B", 100, 10)

        self.assertTrue(self.ob.cancel(1))
        self.assertFalse(self.ob.cancel(1))

        with self.assertRaises(IndexError):
            self.ob.best_bid()

    def test_cancel_nonexistent_order(self):

        self.assertFalse(self.ob.cancel(999))

    def test_cancelled_order_not_matched(self):

        self.ob.add_limit(1, "B", 100, 10)
        self.ob.cancel(1)

        self.assertEqual(
            self.ob.add_limit(2, "S", 100, 5),
            []
        )

        self.assertEqual(self.ob.best_ask(), 100)

    def test_cancel_after_partial_fill(self):

        self.ob.add_limit(1, "S", 100, 10)
        self.ob.add_limit(2, "B", 100, 4)

        self.assertTrue(self.ob.cancel(1))

        with self.assertRaises(IndexError):
            self.ob.best_ask()

        self.assertEqual(
            self.ob.add_limit(3, "B", 100, 5),
            []
        )

    def test_cancel_fully_filled_order_returns_false(self):

        self.ob.add_limit(1, "S", 100, 5)
        self.ob.add_limit(2, "B", 100, 5)

        self.assertFalse(self.ob.cancel(1))
        self.assertFalse(self.ob.cancel(2))

    # ---------- lazy-deletion risks ----------

    def test_best_price_prunes_cancelled_best(self):

        self.ob.add_limit(1, "B", 101, 5)
        self.ob.add_limit(2, "B", 100, 5)
        self.ob.add_limit(3, "S", 110, 5)
        self.ob.add_limit(4, "S", 111, 5)

        self.ob.cancel(1)
        self.ob.cancel(3)

        self.assertEqual(self.ob.best_bid(), 100)
        self.assertEqual(self.ob.best_ask(), 111)

    def test_cancel_front_of_queue_then_match(self):

        self.ob.add_limit(1, "S", 100, 5)
        self.ob.add_limit(2, "S", 100, 5)

        self.ob.cancel(1)

        self.assertEqual(
            self.ob.add_limit(3, "B", 100, 5),
            [(3, 2, 100, 5)]
        )

    def test_cancel_middle_of_queue_keeps_fifo(self):

        self.ob.add_limit(1, "B", 100, 5)
        self.ob.add_limit(2, "B", 100, 5)
        self.ob.add_limit(3, "B", 100, 5)

        self.ob.cancel(2)

        self.assertEqual(
            self.ob.add_limit(4, "S", 100, 10),
            [(1, 4, 100, 5), (3, 4, 100, 5)]
        )

    def test_cancel_whole_level_then_recreate(self):

        self.ob.add_limit(1, "B", 100, 5)
        self.ob.add_limit(2, "B", 100, 5)

        self.ob.cancel(1)
        self.ob.cancel(2)

        with self.assertRaises(IndexError):
            self.ob.best_bid()

        self.ob.add_limit(3, "B", 100, 5)

        self.assertEqual(self.ob.best_bid(), 100)

        self.assertEqual(
            self.ob.add_limit(4, "S", 100, 5),
            [(3, 4, 100, 5)]
        )

    def test_level_emptied_by_fill_then_recreate(self):

        self.ob.add_limit(1, "S", 100, 5)
        self.ob.add_limit(2, "B", 100, 5)

        self.ob.add_limit(3, "S", 100, 7)

        self.assertEqual(self.ob.best_ask(), 100)

        self.assertEqual(
            self.ob.add_limit(4, "B", 100, 7),
            [(4, 3, 100, 7)]
        )

    def test_match_walks_past_cancelled_level(self):

        self.ob.add_limit(1, "S", 100, 5)
        self.ob.add_limit(2, "S", 101, 5)

        self.ob.cancel(1)

        self.assertEqual(
            self.ob.add_limit(3, "B", 101, 5),
            [(3, 2, 101, 5)]
        )

    def test_cancel_all_then_book_empty(self):

        self.ob.add_limit(1, "B", 99, 5)
        self.ob.add_limit(2, "B", 100, 5)
        self.ob.add_limit(3, "S", 105, 5)
        self.ob.add_limit(4, "S", 106, 5)

        for i in range(1, 5):
            self.assertTrue(self.ob.cancel(i))

        with self.assertRaises(IndexError):
            self.ob.best_bid()

        with self.assertRaises(IndexError):
            self.ob.best_ask()

        self.assertEqual(
            self.ob.add_limit(5, "B", 200, 5),
            []
        )

    def test_best_bid_empty_book(self):
        with self.assertRaises(IndexError):
            self.ob.best_bid()

    def test_best_ask_empty_book(self):
        with self.assertRaises(IndexError):
            self.ob.best_ask()


if __name__ == "__main__":
    unittest.main()