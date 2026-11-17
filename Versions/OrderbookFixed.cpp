// Same heap-of-orders algorithm as Orderbook.cpp, written idiomatically:
// fixed-size array entries, unordered_map, one lookup per fill.
#include <algorithm>
#include <array>
#include <stdexcept>
#include <unordered_map>
#include <vector>

class Orderbook {
public:
    using Entry = std::array<int, 3>;  // {price (negated for asks), seq, order_id}
    struct OrderInfo { char side; int price; int qty; };

    std::vector<Entry> bids;   // max heap
    std::vector<Entry> asks;   // max heap on -price
    std::unordered_map<int, OrderInfo> orders;
    int seq = 0;

    std::vector<std::array<int, 4>> add_limit(int order_id, char side, int price, int qty) {
        std::vector<std::array<int, 4>> fills;
        const bool buy = (side == 'B');
        std::vector<Entry>& book = buy ? asks : bids;

        while (qty > 0 && !book.empty()) {
            prune(book);

            if (book.empty())
                break;
            const int best = buy ? -book[0][0] : book[0][0];
            if (buy ? best > price : best < price) break;

            const int resting_id = book[0][2];
            auto it = orders.find(resting_id);
            OrderInfo& r = it->second;

            const int traded = std::min(qty, r.qty);
            qty -= traded;
            r.qty -= traded;

            fills.push_back(buy ? std::array<int, 4>{order_id, resting_id, r.price, traded}
                                : std::array<int, 4>{resting_id, order_id, r.price, traded});

            if (r.qty == 0) {
                std::pop_heap(book.begin(), book.end());
                book.pop_back();
                orders.erase(it);
            }
        }

        if (qty > 0) {
            orders[order_id] = {side, price, qty};
            if (buy) {
                bids.push_back({price, seq, order_id});
                std::push_heap(bids.begin(), bids.end());
            } else {
                asks.push_back({-price, seq, order_id});
                std::push_heap(asks.begin(), asks.end());
            }
            --seq;
        }
        return fills;
    }

    void prune(std::vector<Entry>& book) {
        while (!book.empty() &&
            orders.count(book[0][2]) == 0) {
            std::pop_heap(book.begin(), book.end());
            book.pop_back();
        }
    }
    bool cancel(int order_id) {
        return orders.erase(order_id) > 0;
    }
    int best_bid() {
        if (bids.empty()) throw std::out_of_range("empty bid book");
        return bids[0][0];
    }

    int best_ask() {
        if (asks.empty()) throw std::out_of_range("empty ask book");
        return -asks[0][0];
    }
};