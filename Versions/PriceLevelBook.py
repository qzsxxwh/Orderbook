from collections import deque
from heapq import heappush, heappop


class PriceLevelBook:
    """Price-level book: price -> FIFO queue of order ids, plus a heap of
    distinct prices. Cancel is lazy (O(1)): the order is removed from
    `orders` and skipped when it reaches the front of its queue.
    Assumes order ids are never reused."""

    def __init__(self):
        self.bid_levels = {}    # price -> deque of order_ids
        self.ask_levels = {}
        self.bid_prices = []    # heap of -price
        self.ask_prices = []    # heap of price
        self.orders = {}        # order_id -> [side, price, remaining_qty]

    def _best_live(self, levels, prices, sign):
        """Drop dead orders / empty levels from the front, return best live price."""
        orders = self.orders
        while prices:
            p = sign * prices[0]
            q = levels.get(p)
            if q is not None:
                while q and q[0] not in orders:
                    q.popleft()
                if q:
                    return p
                del levels[p]
            heappop(prices)
        return None

    def add_limit(self, order_id, side, price, qty):
        fills = []
        buy = side == "B"
        if buy:
            levels, prices, sign = self.ask_levels, self.ask_prices, 1
        else:
            levels, prices, sign = self.bid_levels, self.bid_prices, -1
        orders = self.orders

        while qty > 0:
            best = self._best_live(levels, prices, sign)
            if best is None or (best > price if buy else best < price):
                break

            q = levels[best]
            resting_id = q[0]
            r = orders[resting_id]

            traded = min(qty, r[2])
            qty -= traded
            r[2] -= traded

            if buy:
                fills.append((order_id, resting_id, r[1], traded))
            else:
                fills.append((resting_id, order_id, r[1], traded))

            if r[2] == 0:
                del orders[resting_id]
                q.popleft()

        if qty > 0:
            orders[order_id] = [side, price, qty]
            if buy:
                levels, prices, sign = self.bid_levels, self.bid_prices, -1
            else:
                levels, prices, sign = self.ask_levels, self.ask_prices, 1
            q = levels.get(price)
            if q is None:
                q = levels[price] = deque()
                heappush(prices, sign * price)
            q.append(order_id)

        return fills

    def cancel(self, order_id):
        return self.orders.pop(order_id, None) is not None

    def best_bid(self):
        p = self._best_live(self.bid_levels, self.bid_prices, -1)
        if p is None:
            raise IndexError("empty bid book")
        return p

    def best_ask(self):
        p = self._best_live(self.ask_levels, self.ask_prices, 1)
        if p is None:
            raise IndexError("empty ask book")
        return p