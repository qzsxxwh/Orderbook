

def process_orders(trades) :

    out = {}

    for trade in trades:

        info = trade.split(",")
        if len(info) != 5:
            continue

        symbol, side, price, qty = info[1], info[2], info[3], info[4]

        if side != "BUY":
            continue

        volume = int(qty)*int(price)
        if symbol in out:
            out[symbol] += volume
        else:
            out[symbol] = volume

    out_list = []
    for symbol, volume in out.items():
        out_list.append(f"{symbol}:{volume}")

    return sorted(out_list, key=lambda x: x.split(':')[0])

trades = [
    "T1,AAPL,BUY,150,10",
    "T2,MSFT,SELL,300,5",
    "T3,AAPL,BUY,152,5",
    "T4,GOOG,BUY,2800,2",
    "T5,MSFT,BUY,295,10"
]

print(process_orders(trades))