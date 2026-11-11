from Orderbook import OrderBook
import unittest

class TestOrderBook(unittest.TestCase):

    def setUp(self):
        self.ob = OrderBook()

    def test_buy_added_to_book(self):
        fills = self.ob.add_limit(1, "B", 100, 10)

        self.assertEqual(fills, [])

        self.assertEqual(
            self.ob.orders[1],
            ["B", 100, 10]
        )

        self.assertEqual(
            self.ob.best_bid(),
            100
        )

    def test_sell_added_to_book(self):
        fills = self.ob.add_limit(1, "S", 100, 10)

        self.assertEqual(fills, [])

        self.assertEqual(
            self.ob.orders[1],
            ["S", 100, 10]
        )

        self.assertEqual(
            self.ob.best_ask(),
            100
        )

    def test_no_match(self):
        self.ob.add_limit(1, "S", 105, 10)

        fills = self.ob.add_limit(2, "B", 100, 10)

        self.assertEqual(fills, [])

        self.assertIn(1, self.ob.orders)
        self.assertIn(2, self.ob.orders)

    def test_exact_fill(self):
        self.ob.add_limit(1, "S", 100, 10)

        fills = self.ob.add_limit(2, "B", 100, 10)

        self.assertEqual(
            fills,
            [(2, 1, 100, 10)]
        )

        self.assertEqual(
            len(self.ob.orders),
            0
        )

    def test_partial_fill_resting_survives(self):
        self.ob.add_limit(1, "S", 100, 20)

        fills = self.ob.add_limit(2, "B", 100, 5)

        self.assertEqual(
            fills,
            [(2, 1, 100, 5)]
        )

        self.assertEqual(
            self.ob.orders[1],
            ["S", 100, 15]
        )

    def test_partial_fill_incoming_survives(self):
        self.ob.add_limit(1, "S", 100, 5)

        fills = self.ob.add_limit(2, "B", 100, 20)

        self.assertEqual(
            fills,
            [(2, 1, 100, 5)]
        )

        self.assertNotIn(1, self.ob.orders)

        self.assertEqual(
            self.ob.orders[2],
            ["B", 100, 15]
        )

    def test_multiple_matches(self):

        self.ob.add_limit(1, "S", 100, 3)
        self.ob.add_limit(2, "S", 101, 4)
        self.ob.add_limit(3, "S", 102, 5)

        fills = self.ob.add_limit(4, "B", 102, 10)

        self.assertEqual(
            fills,
            [
                (4, 1, 100, 3),
                (4, 2, 101, 4),
                (4, 3, 102, 3),
            ]
        )

        self.assertEqual(
            self.ob.orders[3],
            ["S", 102, 2]
        )

    def test_price_priority(self):

        self.ob.add_limit(1, "B", 100, 5)
        self.ob.add_limit(2, "B", 105, 5)

        fills = self.ob.add_limit(3, "S", 90, 5)

        self.assertEqual(
            fills,
            [(2, 3, 105, 5)]
        )

        self.assertNotIn(2, self.ob.orders)

        self.assertIn(1, self.ob.orders)

    def test_time_priority_same_price(self):

        self.ob.add_limit(1, "B", 100, 5)
        self.ob.add_limit(2, "B", 100, 5)

        fills = self.ob.add_limit(3, "S", 100, 7)

        self.assertEqual(
            fills,
            [
                (1, 3, 100, 5),
                (2, 3, 100, 2),
            ]
        )

        self.assertNotIn(1, self.ob.orders)

        self.assertEqual(
            self.ob.orders[2],
            ["B", 100, 3]
        )

    def test_cancel_existing_order(self):

        self.ob.add_limit(1, "B", 100, 10)

        self.assertTrue(
            self.ob.cancel(1)
        )

        self.assertNotIn(
            1,
            self.ob.orders
        )

    def test_cancel_nonexistent_order(self):

        self.assertFalse(
            self.ob.cancel(999)
        )

    def test_cancelled_order_not_matched(self):

        self.ob.add_limit(1, "B", 100, 10)

        self.ob.cancel(1)

        fills = self.ob.add_limit(2, "S", 100, 5)

        self.assertEqual(
            fills,
            []
        )

    def test_cancel_returns_order(self):

        self.ob.add_limit(1, "B", 100, 10)

        self.ob.cancel(1)

        self.assertEqual(
            len(self.ob.orders),
            0
        )

        self.assertEqual(
            len(self.ob.bids),
            0
        )

    def test_best_bid_empty_book(self):
        with self.assertRaises(IndexError):
            self.ob.best_bid()

    def test_best_ask_empty_book(self):
        with self.assertRaises(IndexError):
            self.ob.best_ask()

    def test_cancel_after_partial_fill(self):
        self.ob.add_limit(1, "S", 100, 10)

        self.ob.add_limit(2, "B", 100, 4)

        self.assertTrue(
            self.ob.cancel(1)
        )

        self.assertEqual(
            len(self.ob.orders),
            0
        )

    def test_multiple_orders_same_price_fifo(self):
        self.ob.add_limit(1, "S", 100, 2)
        self.ob.add_limit(2, "S", 100, 2)
        self.ob.add_limit(3, "S", 100, 2)

        fills = self.ob.add_limit(4, "B", 100, 5)

        self.assertEqual(
            fills,
            [
                (4, 1, 100, 2),
                (4, 2, 100, 2),
                (4, 3, 100, 1),
            ]
        )

        self.assertEqual(
            self.ob.orders[3],
            ["S", 100, 1]
        )

if __name__ == "__main__":
    unittest.main()