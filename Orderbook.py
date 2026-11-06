from heapq import *

class OrderBook:
    def __init__(self):
        self.bids = []      # heap of (-price, seq, order_id)
        self.asks = []      # heap of (price, seq, order_id)
        self.orders = {}    # order_id -> [side, price, remaining_qty]
        self.seq = 0

    def add_limit(self, order_id, side, price, qty):
        fills = []
        #case for each side
        match side:
            case "B":
                #init. remaining wanted qty
                remaining_qty = qty
                #as long as best ask is affordable
                while remaining_qty > 0 and len(self.asks) > 0 and self.best_ask() <= price:
                    bought_qty = 0
                    #init best ask seller id and best ask remaining qty
                    seller_id = self.asks[0][2]
                    seller_price = self.orders[seller_id][1]
                    s_remaining_qty = self.orders[seller_id][2]
                    #if seller has less than or as much as buyer needs
                    if s_remaining_qty < remaining_qty:
                        #update buyer remaining wanted qty
                        bought_qty = s_remaining_qty
                        remaining_qty -= s_remaining_qty
                        #all seller's qty depleted -> remove seller from the book
                        self.orders.pop(seller_id)
                        heappop(self.asks)
                    #seller has more than buyer needs
                    elif s_remaining_qty > remaining_qty:
                        #update bought qty
                        bought_qty = remaining_qty
                        #remove what buyer bought from seller's qty
                        s_remaining_qty -= remaining_qty
                        remaining_qty = 0
                    #seller has just as much as buyer needs
                    elif s_remaining_qty == remaining_qty:
                        bought_qty = remaining_qty
                        #both the seller and buyer's qtys are depleted -> remove seller from the book
                        s_remaining_qty, remaining_qty = 0, 0
                        self.orders.pop(seller_id)
                        heappop(self.asks)
                    self.orders[seller_id][2] = s_remaining_qty
                    fills.append((order_id, seller_id, seller_price, bought_qty))
                #buyer still has unbought qty
                if remaining_qty > 0:
                    #add buyer to book
                    heappush(self.bids, (-price, self.seq, order_id))
                    self.orders[order_id] = [side, price, remaining_qty]
            case "S":
                #init. remaining qty
                remaining_seller_qty = qty
                #as long as best offer is enough
                while remaining_seller_qty > 0 and len(self.bids) > 0 and self.best_bid() >= price:
                    pass
        return fills
        # returns list of fills

    def cancel(self, order_id):
        ...  # returns True/False

    def best_bid(self):
        return - self.bids[0][0]

    def best_ask(self):
        return self.asks[0][0]
    

ob = OrderBook()
ob.add_limit(1, "S", 102, 2)
ob.add_limit(2, "S", 101, 14)
ob.add_limit(3, "B", 102, 18)
