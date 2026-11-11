from heapq import *

class OrderBook:
    def __init__(self):
        self.bids = []      # heap of (-price, seq, order_id)
        self.asks = []      # heap of (price, seq, order_id)
        self.orders = {}    # order_id -> [side, price, remaining_qty]
        self.seq = 0

    def _opposite_book(self, side):
        return self.asks if side == "B" else self.bids

    def _best_price(self, side):
        book = self._opposite_book(side)

        if not book:
            return None

        return book[0][0] if side == "B" else -book[0][0]

    def _crosses(self, side, limit_price):
        best = self._best_price(side)

        if best is None:
            return False

        return best <= limit_price if side == "B" else best >= limit_price

    def _add_to_book(self, order_id, side, price, qty):
        self.orders[order_id] = [side, price, qty]

        if side == "B":
            heappush(self.bids, (-price, self.seq, order_id))
        else:
            heappush(self.asks, (price, self.seq, order_id))

        self.seq += 1

    def _make_fill(self, incoming_id, resting_id, side, price, qty):
        if side == "B":
            return (incoming_id, resting_id, price, qty)

        return (resting_id, incoming_id, price, qty)

    def add_limit(self, order_id, side, price, qty):

        fills = []
        remaining = qty

        book = self._opposite_book(side)

        while remaining > 0 and self._crosses(side, price):

            resting_id = book[0][2]

            resting_price = self.orders[resting_id][1]
            resting_qty = self.orders[resting_id][2]

            traded_qty = min(remaining, resting_qty)

            remaining -= traded_qty
            resting_qty -= traded_qty

            fills.append(
                self._make_fill(
                    order_id,
                    resting_id,
                    side,
                    resting_price,
                    traded_qty,
                )
            )

            if resting_qty == 0:
                self.orders.pop(resting_id)
                heappop(book)
            else:
                self.orders[resting_id][2] = resting_qty

        if remaining > 0:
            self._add_to_book(
                order_id,
                side,
                price,
                remaining,
            )

        return fills
        # returns list of fills

    def cancel(self, order_id):
        if order_id in self.orders:
            match self.orders[order_id][0]:
                case"B":
                    for index, bid in enumerate(self.bids):
                        if bid[2] == order_id:
                            self.bids[index] = self.bids[-1]
                            self.bids.pop()
                            heapify(self.bids)
                            break
                case"S":
                    for index, ask in enumerate(self.asks):
                        if ask[2] == order_id:
                            self.asks[index] = self.asks[-1]
                            self.asks.pop()
                            heapify(self.asks)
                            break
            self.orders.pop(order_id)
            return True
        else:
            return False

    def best_bid(self):
        return - self.bids[0][0]

    def best_ask(self):
        return self.asks[0][0]
    
