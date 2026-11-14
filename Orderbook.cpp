#include <iostream>
using namespace std;
#include <vector>
#include <map>
#include <optional>
#include <algorithm>
#include <array>

class Orderbook {
    public:
    vector<vector<int>>  bids;    // heap of (price, seq, order_id)
    vector<vector<int>> asks;     // heap of (-price, seq, order_id)
    struct OrderInfo {
        char side;
        int price;
        int qty;
    }; 
    map<int, OrderInfo> orders;//order_id -> [side, price, remaining_qty]
    int seq = 0;

    vector<vector<int>>& opposite_book(char side) {

        return (side == 'B') ? asks : bids;
    }

    optional<int> best_price(char side) {
        vector<vector<int>>& book = opposite_book(side);

        if (book.empty()) {
            return nullopt;
        }

        int price = book[0][0];
        return (side == 'B') ? -price : price;
    }

    bool crosses(char side, int limit_price) {
        optional<int> best = best_price(side);

        if (!best) {
            return false;
        }

        return (side == 'B') 
        ? *best <= limit_price 
        : *best >= limit_price;
    }

    void add_to_book(int order_id, char side, int price, int qty) {
        orders[order_id] = {side, price, qty};

        if (side == 'B') {
            bids.push_back({price, seq, order_id});
            push_heap(bids.begin(), bids.end());
        }
        else {
            asks.push_back({-price, seq, order_id});
            push_heap(asks.begin(), asks.end());
        }

        seq -= 1;
    }

    array<int, 4> make_fill(int incoming_id, int resting_id, char side, int price, int qty) {
        return (side == 'B') 
        ? array<int, 4>{incoming_id, resting_id, price, qty} 
        : array<int, 4>{resting_id, incoming_id, price, qty};
    }

    vector<array<int, 4>> add_limit(int order_id, char side, int price, int qty) {
        
        vector<array<int, 4>> fills = {};
        int remaining = qty;

        vector<vector<int>>& book = opposite_book(side);

        while (remaining > 0 && crosses(side, price)) {

            int resting_id = book[0][2];

            int resting_price = orders[resting_id].price;
            int resting_qty = orders[resting_id].qty;

            int traded_qty = min(remaining, resting_qty);

            remaining -= traded_qty;
            resting_qty -= traded_qty;

            fills.push_back(
                make_fill(
                    order_id,
                    resting_id,
                    side,
                    resting_price,
                    traded_qty
                )
            );

            if (resting_qty == 0) {
                orders.erase(resting_id);
                pop_heap(book.begin(), book.end());
                book.pop_back();
            }
            else {
                orders[resting_id].qty = resting_qty;
            }
        }

        if (remaining > 0) {
            add_to_book(
                order_id,
                side,
                price,
                remaining
            );
        }

        return fills;

    }

    bool cancel(int order_id) {
    if (orders.count(order_id) == 0) {
        return false;
    }

    switch (orders[order_id].side) {

        case 'B':
            for (size_t i = 0; i < bids.size(); ++i) {
                if (bids[i][2] == order_id) {
                    bids[i] = bids.back();
                    bids.pop_back();

                    make_heap(bids.begin(), bids.end());
                    break;
                }
            }
            break;

        case 'S':
            for (size_t i = 0; i < asks.size(); ++i) {
                if (asks[i][2] == order_id) {
                    asks[i] = asks.back();
                    asks.pop_back();

                    make_heap(asks.begin(), asks.end());
                    break;
                }
            }
            break;
    }

    orders.erase(order_id);

    return true;
}

    int best_bid() {
        if (bids.empty()) {
            throw out_of_range("empty bid book");
        }
        return bids[0][0];
    }

    int best_ask() {
        if (asks.empty()) {
            throw out_of_range("empty ask book");
        }
        return - asks[0][0];
    }
};
