// Same structure as PriceLevelBook.py: price -> FIFO queue of order ids,
// plus a heap of distinct prices, with lazy cancel. Assumes unique order ids.
#include <algorithm>
#include <array>
#include <deque>
#include <functional>
#include <optional>
#include <queue>
#include <stdexcept>
#include <unordered_map>
#include <vector>

class PriceLevelBook {
    struct OrderInfo { char side; int price; int qty; };
    using Levels = std::unordered_map<int, std::deque<int>>;

    Levels bid_levels, ask_levels;
    std::priority_queue<int> bid_prices;                                        // max heap
    std::priority_queue<int, std::vector<int>, std::greater<int>> ask_prices;   // min heap
    std::unordered_map<int, OrderInfo> orders;

    template <class Heap>
    std::optional<int> best_live(Levels& levels, Heap& prices) {
        while (!prices.empty()) {
            const int p = prices.top();
            auto it = levels.find(p);
            if (it != levels.end()) {
                auto& q = it->second;
                while (!q.empty() && !orders.count(q.front())) q.pop_front();
                if (!q.empty()) return p;
                levels.erase(it);
            }
            prices.pop();
        }
        return std::nullopt;
    }

public:
    std::vector<std::array<int, 4>> add_limit(int id, char side, int price, int qty) {
        std::vector<std::array<int, 4>> fills;
        const bool buy = (side == 'B');

        while (qty > 0) {
            auto best = buy ? best_live(ask_levels, ask_prices)
                            : best_live(bid_levels, bid_prices);
            if (!best || (buy ? *best > price : *best < price)) break;

            auto& q = (buy ? ask_levels : bid_levels).find(*best)->second;
            const int rid = q.front();
            auto it = orders.find(rid);
            OrderInfo& r = it->second;

            const int traded = std::min(qty, r.qty);
            qty -= traded;
            r.qty -= traded;
            fills.push_back(buy ? std::array<int, 4>{id, rid, r.price, traded}
                                : std::array<int, 4>{rid, id, r.price, traded});

            if (r.qty == 0) {
                orders.erase(it);
                q.pop_front();
            }
        }

        if (qty > 0) {
            orders[id] = {side, price, qty};
            auto& levels = buy ? bid_levels : ask_levels;
            auto [lvl, created] = levels.try_emplace(price);
            if (created) {
                if (buy) bid_prices.push(price); else ask_prices.push(price);
            }
            lvl->second.push_back(id);
        }
        return fills;
    }

    bool cancel(int id) { return orders.erase(id) > 0; }

    int best_bid() {
        auto b = best_live(bid_levels, bid_prices);
        if (!b) throw std::out_of_range("empty bid book");
        return *b;
    }

    int best_ask() {
        auto a = best_live(ask_levels, ask_prices);
        if (!a) throw std::out_of_range("empty ask book");
        return *a;
    }
};