// C++ harness. One binary per book, chosen at compile time (see run_all.py):
//   g++ -O2 -std=c++17 -I . -DUSE_PRICELEVEL bench.cpp -o bench_cpp_pricelevel
// Usage: ./bench_cpp_pricelevel workloads/p100_c30.txt 5 results.csv
// CSV row: impl,workload,run,ns,ops,fills,traded,cancel_hits,best_bid,best_ask
#include <array>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

// Which book to benchmark is picked at compile time with -DUSE_ORIG, -DUSE_FIXED or
// -DUSE_PRICELEVEL (run_all.py does this). With no flag, the editor sees PriceLevelBook.
#if defined(USE_ORIG)
#include "../Versions/Orderbook.cpp"
#define BOOK_CLASS Orderbook
#define BOOK_NAME "cpp_orig"
#elif defined(USE_FIXED)
#include "../Versions/OrderbookFixed.cpp"
#define BOOK_CLASS Orderbook
#define BOOK_NAME "cpp_fixed"
#else
#include "../Versions/PriceLevelBook.cpp"
#define BOOK_CLASS PriceLevelBook
#define BOOK_NAME "cpp_pricelevel"
#endif

struct Op { int kind; int id; char side; int price; int qty; };

struct Result { long long ns, fills, traded, hits; int bb, ba; };

static std::vector<Op> load(const std::string& path) {
    std::vector<Op> ops;
    std::ifstream in(path);
    char kind;
    while (in >> kind) {
        Op op{};
        if (kind == 'A') { op.kind = 0; in >> op.id >> op.side >> op.price >> op.qty; }
        else             { op.kind = 1; in >> op.id; }
        ops.push_back(op);
    }
    return ops;
}

static Result run(const std::vector<Op>& ops, size_t n) {
    BOOK_CLASS book;
    long long fills = 0, traded = 0, hits = 0;
    auto t0 = std::chrono::steady_clock::now();
    for (size_t i = 0; i < n; ++i) {
        const Op& op = ops[i];
        if (op.kind == 0) {
            auto f = book.add_limit(op.id, op.side, op.price, op.qty);
            fills += (long long)f.size();
            for (auto& x : f) traded += x[3];
        } else if (book.cancel(op.id)) {
            ++hits;
        }
    }
    auto t1 = std::chrono::steady_clock::now();
    int bb = -1, ba = -1;
    try { bb = book.best_bid(); } catch (const std::out_of_range&) {}
    try { ba = book.best_ask(); } catch (const std::out_of_range&) {}
    long long ns = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
    return {ns, fills, traded, hits, bb, ba};
}

int main(int argc, char** argv) {
    if (argc < 4) { std::fprintf(stderr, "usage: %s workload runs csv\n", argv[0]); return 1; }
    std::string path = argv[1];
    int runs = std::atoi(argv[2]);
    std::vector<Op> ops = load(path);

    std::string name = path.substr(path.find_last_of("/\\") == std::string::npos ? 0
                                   : path.find_last_of("/\\") + 1);
    name = name.substr(0, name.find_last_of('.'));

    run(ops, std::min<size_t>(ops.size(), 10000));          // warm-up
    std::ofstream out(argv[3], std::ios::app);
    double last = 0;
    for (int r = 0; r < runs; ++r) {
        Result x = run(ops, ops.size());
        out << BOOK_NAME << ',' << name << ',' << r << ',' << x.ns << ',' << ops.size()
            << ',' << x.fills << ',' << x.traded << ',' << x.hits << ',' << x.bb << ',' << x.ba << '\n';
        last = x.ns / 1e9;
    }
    std::printf("%-14s %s: last run %.3fs\n", BOOK_NAME, name.c_str(), last);
}