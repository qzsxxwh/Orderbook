#include <cassert>
#include <iostream>
#include <stdexcept>
#include "../Versions/OrderbookFixed.cpp"

using namespace std;

void test_buy_added_to_book() {
    Orderbook ob;

    auto fills = ob.add_limit(1, 'B', 100, 10);

    assert(fills.empty());

    assert(ob.orders[1].side == 'B');
    assert(ob.orders[1].price == 100);
    assert(ob.orders[1].qty == 10);

    assert(ob.best_bid() == 100);
}

void test_sell_added_to_book() {
    Orderbook ob;

    auto fills = ob.add_limit(1, 'S', 100, 10);

    assert(fills.empty());

    assert(ob.orders[1].side == 'S');
    assert(ob.orders[1].price == 100);
    assert(ob.orders[1].qty == 10);

    assert(ob.best_ask() == 100);
}

void test_no_match() {
    Orderbook ob;

    ob.add_limit(1, 'S', 105, 10);

    auto fills = ob.add_limit(2, 'B', 100, 10);

    assert(fills.empty());

    assert(ob.orders.count(1));
    assert(ob.orders.count(2));
}

void test_exact_fill() {
    Orderbook ob;

    ob.add_limit(1, 'S', 100, 10);

    auto fills = ob.add_limit(2, 'B', 100, 10);

    vector<array<int,4>> expected = {
        {2,1,100,10}
    };

    assert(fills == expected);
    assert(ob.orders.empty());
}

void test_partial_fill_resting_survives() {
    Orderbook ob;

    ob.add_limit(1, 'S', 100, 20);

    auto fills = ob.add_limit(2, 'B', 100, 5);

    vector<array<int,4>> expected = {
        {2,1,100,5}
    };

    assert(fills == expected);

    assert(ob.orders[1].side == 'S');
    assert(ob.orders[1].price == 100);
    assert(ob.orders[1].qty == 15);
}

void test_partial_fill_incoming_survives() {
    Orderbook ob;

    ob.add_limit(1, 'S', 100, 5);

    auto fills = ob.add_limit(2, 'B', 100, 20);

    vector<array<int,4>> expected = {
        {2,1,100,5}
    };

    assert(fills == expected);

    assert(!ob.orders.count(1));

    assert(ob.orders[2].side == 'B');
    assert(ob.orders[2].price == 100);
    assert(ob.orders[2].qty == 15);
}

void test_multiple_matches() {
    Orderbook ob;

    ob.add_limit(1, 'S', 100, 3);
    ob.add_limit(2, 'S', 101, 4);
    ob.add_limit(3, 'S', 102, 5);

    auto fills = ob.add_limit(4, 'B', 102, 10);

    vector<array<int,4>> expected = {
        {4,1,100,3},
        {4,2,101,4},
        {4,3,102,3}
    };

    assert(fills == expected);

    assert(ob.orders[3].side == 'S');
    assert(ob.orders[3].price == 102);
    assert(ob.orders[3].qty == 2);
}

void test_price_priority() {
    Orderbook ob;

    ob.add_limit(1, 'B', 100, 5);
    ob.add_limit(2, 'B', 105, 5);

    auto fills = ob.add_limit(3, 'S', 90, 5);

    vector<array<int,4>> expected = {
        {2,3,105,5}
    };

    assert(fills == expected);

    assert(!ob.orders.count(2));
    assert(ob.orders.count(1));
}

void test_time_priority_same_price() {
    Orderbook ob;

    ob.add_limit(1, 'B', 100, 5);
    ob.add_limit(2, 'B', 100, 5);

    auto fills = ob.add_limit(3, 'S', 100, 7);

    vector<array<int,4>> expected = {
        {1,3,100,5},
        {2,3,100,2}
    };

    assert(fills == expected);

    assert(!ob.orders.count(1));

    assert(ob.orders[2].side == 'B');
    assert(ob.orders[2].price == 100);
    assert(ob.orders[2].qty == 3);
}

void test_cancel_existing_order() {
    Orderbook ob;

    ob.add_limit(1, 'B', 100, 10);

    assert(ob.cancel(1));
    assert(!ob.orders.count(1));
}

void test_cancel_nonexistent_order() {
    Orderbook ob;

    assert(!ob.cancel(999));
}

void test_cancelled_order_not_matched() {
    Orderbook ob;

    ob.add_limit(1, 'B', 100, 10);

    ob.cancel(1);

    auto fills = ob.add_limit(2, 'S', 100, 5);

    assert(fills.empty());
}

void test_best_bid_empty_book() {
    Orderbook ob;

    bool threw = false;

    try {
        ob.best_bid();
    }
    catch (const out_of_range&) {
        threw = true;
    }

    assert(threw);
}

void test_best_ask_empty_book() {
    Orderbook ob;

    bool threw = false;

    try {
        ob.best_ask();
    }
    catch (const out_of_range&) {
        threw = true;
    }

    assert(threw);
}

void test_cancel_after_partial_fill() {
    Orderbook ob;

    ob.add_limit(1, 'S', 100, 10);
    ob.add_limit(2, 'B', 100, 4);

    assert(ob.cancel(1));

    assert(ob.orders.empty());
}

void test_multiple_orders_same_price_fifo() {
    Orderbook ob;

    ob.add_limit(1, 'S', 100, 2);
    ob.add_limit(2, 'S', 100, 2);
    ob.add_limit(3, 'S', 100, 2);

    auto fills = ob.add_limit(4, 'B', 100, 5);

    vector<array<int,4>> expected = {
        {4,1,100,2},
        {4,2,100,2},
        {4,3,100,1}
    };

    assert(fills == expected);

    assert(ob.orders[3].side == 'S');
    assert(ob.orders[3].price == 100);
    assert(ob.orders[3].qty == 1);
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
    test_cancel_existing_order();
    test_cancel_nonexistent_order();
    test_cancelled_order_not_matched();
    test_best_bid_empty_book();
    test_best_ask_empty_book();
    test_cancel_after_partial_fill();
    test_multiple_orders_same_price_fifo();

    cout << "All tests passed!" << endl;
}