// Public-interface tests for PriceLevelBook (add_limit, cancel, best_bid, best_ask).
// Build: g++ -std=c++17 -O0 test_PriceLevelBook.cpp -o test_plb && ./test_plb
#include <array>
#include <cassert>
#include <iostream>
#include <stdexcept>
#include <vector>
#include "../Versions/PriceLevelBook.cpp"

using namespace std;
using Fills = vector<array<int, 4>>;   // {buy_id, sell_id, price, qty}

template <class F>
bool throws_out_of_range(F f) {
    try { f(); } catch (const out_of_range&) { return true; }
    return false;
}

// ---------- basic behavior ----------

void test_buy_added_to_book() {
    PriceLevelBook ob;
    assert(ob.add_limit(1, 'B', 100, 10).empty());
    assert(ob.best_bid() == 100);
}

void test_sell_added_to_book() {
    PriceLevelBook ob;
    assert(ob.add_limit(1, 'S', 100, 10).empty());
    assert(ob.best_ask() == 100);
}

void test_no_match() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 105, 10);
    assert(ob.add_limit(2, 'B', 100, 10).empty());
    assert(ob.best_ask() == 105);
    assert(ob.best_bid() == 100);
}

void test_exact_fill() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 10);
    assert(ob.add_limit(2, 'B', 100, 10) == (Fills{{2, 1, 100, 10}}));
    assert(throws_out_of_range([&] { ob.best_ask(); }));
    assert(throws_out_of_range([&] { ob.best_bid(); }));
}

void test_partial_fill_resting_survives() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 20);
    assert(ob.add_limit(2, 'B', 100, 5) == (Fills{{2, 1, 100, 5}}));
    assert(ob.best_ask() == 100);
    // 15 must remain
    assert(ob.add_limit(3, 'B', 100, 50) == (Fills{{3, 1, 100, 15}}));
}

void test_partial_fill_incoming_survives() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 5);
    assert(ob.add_limit(2, 'B', 100, 20) == (Fills{{2, 1, 100, 5}}));
    assert(ob.best_bid() == 100);
    assert(throws_out_of_range([&] { ob.best_ask(); }));
    // 15 must remain
    assert(ob.add_limit(3, 'S', 100, 50) == (Fills{{2, 3, 100, 15}}));
}

void test_multiple_matches() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 3);
    ob.add_limit(2, 'S', 101, 4);
    ob.add_limit(3, 'S', 102, 5);
    assert(ob.add_limit(4, 'B', 102, 10) ==
           (Fills{{4, 1, 100, 3}, {4, 2, 101, 4}, {4, 3, 102, 3}}));
    assert(ob.best_ask() == 102);
    assert(ob.add_limit(5, 'B', 102, 50) == (Fills{{5, 3, 102, 2}}));
}

void test_price_priority() {
    PriceLevelBook ob;
    ob.add_limit(1, 'B', 100, 5);
    ob.add_limit(2, 'B', 105, 5);
    assert(ob.add_limit(3, 'S', 90, 5) == (Fills{{2, 3, 105, 5}}));
    assert(ob.best_bid() == 100);
}

void test_time_priority_same_price() {
    PriceLevelBook ob;
    ob.add_limit(1, 'B', 100, 5);
    ob.add_limit(2, 'B', 100, 5);
    assert(ob.add_limit(3, 'S', 100, 7) == (Fills{{1, 3, 100, 5}, {2, 3, 100, 2}}));
    assert(ob.add_limit(4, 'S', 100, 50) == (Fills{{2, 4, 100, 3}}));
}

void test_multiple_orders_same_price_fifo() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 2);
    ob.add_limit(2, 'S', 100, 2);
    ob.add_limit(3, 'S', 100, 2);
    assert(ob.add_limit(4, 'B', 100, 5) ==
           (Fills{{4, 1, 100, 2}, {4, 2, 100, 2}, {4, 3, 100, 1}}));
    assert(ob.add_limit(5, 'B', 100, 50) == (Fills{{5, 3, 100, 1}}));
}

void test_fill_price_is_resting_price() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 5);
    assert(ob.add_limit(2, 'B', 110, 5) == (Fills{{2, 1, 100, 5}}));
}

// ---------- cancel ----------

void test_cancel_existing_order() {
    PriceLevelBook ob;
    ob.add_limit(1, 'B', 100, 10);
    assert(ob.cancel(1));
    assert(!ob.cancel(1));                       // already gone
    assert(throws_out_of_range([&] { ob.best_bid(); }));
}

void test_cancel_nonexistent_order() {
    PriceLevelBook ob;
    assert(!ob.cancel(999));
}

void test_cancelled_order_not_matched() {
    PriceLevelBook ob;
    ob.add_limit(1, 'B', 100, 10);
    ob.cancel(1);
    assert(ob.add_limit(2, 'S', 100, 5).empty());
    assert(ob.best_ask() == 100);
}

void test_cancel_after_partial_fill() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 10);
    ob.add_limit(2, 'B', 100, 4);
    assert(ob.cancel(1));
    assert(throws_out_of_range([&] { ob.best_ask(); }));
    assert(ob.add_limit(3, 'B', 100, 5).empty());   // nothing left to match
}

void test_cancel_fully_filled_order_returns_false() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 5);
    ob.add_limit(2, 'B', 100, 5);
    assert(!ob.cancel(1));
    assert(!ob.cancel(2));
}

// ---------- lazy-deletion risks ----------

void test_best_price_prunes_cancelled_best() {
    PriceLevelBook ob;
    ob.add_limit(1, 'B', 101, 5);
    ob.add_limit(2, 'B', 100, 5);
    ob.add_limit(3, 'S', 110, 5);
    ob.add_limit(4, 'S', 111, 5);
    ob.cancel(1);
    ob.cancel(3);
    assert(ob.best_bid() == 100);
    assert(ob.best_ask() == 111);
}

void test_cancel_front_of_queue_then_match() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 5);
    ob.add_limit(2, 'S', 100, 5);
    ob.cancel(1);
    assert(ob.add_limit(3, 'B', 100, 5) == (Fills{{3, 2, 100, 5}}));
}

void test_cancel_middle_of_queue_keeps_fifo() {
    PriceLevelBook ob;
    ob.add_limit(1, 'B', 100, 5);
    ob.add_limit(2, 'B', 100, 5);
    ob.add_limit(3, 'B', 100, 5);
    ob.cancel(2);
    assert(ob.add_limit(4, 'S', 100, 10) == (Fills{{1, 4, 100, 5}, {3, 4, 100, 5}}));
}

void test_cancel_whole_level_then_recreate() {
    PriceLevelBook ob;
    ob.add_limit(1, 'B', 100, 5);
    ob.add_limit(2, 'B', 100, 5);
    ob.cancel(1);
    ob.cancel(2);
    assert(throws_out_of_range([&] { ob.best_bid(); }));
    ob.add_limit(3, 'B', 100, 5);
    assert(ob.best_bid() == 100);
    assert(ob.add_limit(4, 'S', 100, 5) == (Fills{{3, 4, 100, 5}}));
}

void test_level_emptied_by_fill_then_recreate() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 5);
    ob.add_limit(2, 'B', 100, 5);               // empties the level
    ob.add_limit(3, 'S', 100, 7);
    assert(ob.best_ask() == 100);
    assert(ob.add_limit(4, 'B', 100, 7) == (Fills{{4, 3, 100, 7}}));
}

void test_match_walks_past_cancelled_level() {
    PriceLevelBook ob;
    ob.add_limit(1, 'S', 100, 5);
    ob.add_limit(2, 'S', 101, 5);
    ob.cancel(1);
    assert(ob.add_limit(3, 'B', 101, 5) == (Fills{{3, 2, 101, 5}}));
}

void test_cancel_all_then_book_empty() {
    PriceLevelBook ob;
    ob.add_limit(1, 'B', 99, 5);
    ob.add_limit(2, 'B', 100, 5);
    ob.add_limit(3, 'S', 105, 5);
    ob.add_limit(4, 'S', 106, 5);
    for (int id = 1; id <= 4; ++id) assert(ob.cancel(id));
    assert(throws_out_of_range([&] { ob.best_bid(); }));
    assert(throws_out_of_range([&] { ob.best_ask(); }));
    assert(ob.add_limit(5, 'B', 200, 5).empty());   // nothing to cross
}

// ---------- empty book ----------

void test_best_bid_empty_book() {
    PriceLevelBook ob;
    assert(throws_out_of_range([&] { ob.best_bid(); }));
}

void test_best_ask_empty_book() {
    PriceLevelBook ob;
    assert(throws_out_of_range([&] { ob.best_ask(); }));
}

int main() {
    test_buy_added_to_book();
    test_sell_added_to_book();
    test_no_match();
    test_exact_fill();
    test_partial_fill_resting_survives();
    test_partial_fill_incoming_survives();
    test_multiple_matches();
    test_price_priority();
    test_time_priority_same_price();
    test_multiple_orders_same_price_fifo();
    test_fill_price_is_resting_price();
    test_cancel_existing_order();
    test_cancel_nonexistent_order();
    test_cancelled_order_not_matched();
    test_cancel_after_partial_fill();
    test_cancel_fully_filled_order_returns_false();
    test_best_price_prunes_cancelled_best();
    test_cancel_front_of_queue_then_match();
    test_cancel_middle_of_queue_keeps_fifo();
    test_cancel_whole_level_then_recreate();
    test_level_emptied_by_fill_then_recreate();
    test_match_walks_past_cancelled_level();
    test_cancel_all_then_book_empty();
    test_best_bid_empty_book();
    test_best_ask_empty_book();
    cout << "All tests passed!" << endl;
}