import pandas as pd
import time
from cexapi import API


def buy_bitcoin(bitcoin_amount, last_price):
    """Get last bids and asks (buying/selling prices)
    based on last prices we make our price a little
    bigger than last price (makers pay lower fees,
    maker – make an order that someone else is going to fill)
    """
    tries = 0
    bitcoin_order_price = 0.0
    last_bid = access_api.order_book('BTC/USD')['bids'][0][0]
    last_ask = access_api.order_book('BTC/USD')['asks'][0][0]

    while (last_bid - last_price) < 10:
        if len(access_api.current_orders('BTC/USD')) != 0:
            access_api.cancel_order(int(access_api.current_orders('BTC/USD')[0]['id']))
        elif bitcoin_order_price > 1.0:
            return (True, bitcoin_order_price)

        order_book_dict = access_api.order_book('BTC/USD')
        if ('bids' in order_book_dict) and ('asks' in order_book_dict):
            last_bid = order_book_dict['bids'][0][0]
            last_ask = order_book_dict['asks'][0][0]
            bid_ask_diff = last_ask - last_bid

            if (bid_ask_diff > 0.0):
                if bid_ask_diff > 1.0:
                    bitcoin_order_price = last_bid + 1.0
                else:
                    bitcoin_order_price = last_bid - 0.5
            access_api.place_order('buy', bitcoin_amount, bitcoin_order_price, 'BTC/USD')

        tries += 1
        if tries == 3:
            break
        time.sleep(1)
    return (False, 0.0)


def sell_bitcoin(bitcoin_amount, last_price):
    """Get last bids and asks (buying/selling prices)
    based on last prices we make our price a little
    lower than last price (makers pay lower fees,
    maker – make an order that someone else is going to fill)
    """
    tries = 0
    bitcoin_order_price = 0.0
    last_bid = access_api.order_book('BTC/USD')['bids'][0][0]
    last_ask = access_api.order_book('BTC/USD')['asks'][0][0]

    while (last_ask > (last_price + 5)):
        if len(access_api.current_orders('BTC/USD')) != 0:
            access_api.cancel_order(int(access_api.current_orders('BTC/USD')[0]['id']))
        elif bitcoin_order_price > 1.0:
            return (True, bitcoin_order_price)

        order_book_dict = access_api.order_book('BTC/USD')
        if ('bids' in order_book_dict) and ('asks' in order_book_dict):
            last_bid = order_book_dict['bids'][0][0]
            last_ask = order_book_dict['asks'][0][0]
            bid_ask_diff = last_ask - last_bid

            if (bid_ask_diff > 0.0):
                if bid_ask_diff > 1.0:
                    bitcoin_order_price = last_ask - 1.0
                else:
                    bitcoin_order_price = last_ask + 0.5
            access_api.place_order('sell', bitcoin_amount, bitcoin_order_price, 'BTC/USD')

        tries += 1
        if tries == 3:
            break
        time.sleep(1)
    return (False, 0.0)


def main():
    bitcoin_amount = 0.01  # how much bitcoin we trade ?
    buy = False  # Do we need to buy/sell bitcoin?
    last_price = 0.0
    username = ''
    api_key = ''
    api_secret = ''

    # create class object to access cex.io API
    access_api = API(username, api_key, api_secret)

    # setting DataFrame index and columns name
    index = [0]
    columns = ['price', 'ema_short', 'ema_long']

    # pandas DataFrame initialization
    df = pd.DataFrame(index=index, columns=columns)

    # fill DataFrame with data of last hour
    last_hour_prices = access_api.price_stats(1, 100, couple='BTC/USD')
    for price in last_hour_prices:
        if 'price' in price:
            # add bitcoin last price to DataFrame
            df.loc[df.index.max() + 1] = [float(price['price']), None, None]
    last_price = df.iloc[-1, 0]

    # get price every minute and store in pandas DataFrame, calculate
    # two EMA (exponential moving average): one with shorter time frame
    # and another with long time frame, and when price crosses MA (moving average)
    # we buy or sell bitcoin
    print('Start of trading ...')
    while True:
        ticker_dict = access_api.ticker('BTC/USD')
        # price changed
        if 'last' in ticker_dict and last_price != float(ticker_dict['last']):
            # add bitcoin price to DataFrame
            df.loc[df.index.max() + 1] = [float(ticker_dict['last']), 0, 0]
            # calculate EMA with shorter time frame - 5
            df['ema_short'] = df['price'].ewm(span=5, min_periods=5, adjust=False).mean()
            # calculate EMA with longer time frame - 21
            df['ema_long'] = df['price'].ewm(span=21, min_periods=21, adjust=False).mean()
            last_price = float(ticker_dict['last'])
            print('Bitcoin price:', last_price)

            # when the shorter-term MA crosses above the longer-term MA, it's a buy signal
            if not buy and (df.iloc[-1, 1] < df.iloc[-1, 2]):
                print('Buying bitcoin')
                # tuple(bool: bought or not, buy price)
                buy_status_tuple = buy_bitcoin(bitcoin_amount, df.iloc[-1, 0])
                if buy_status_tuple[0]:
                    buy = True

            # when the shorter-term MA crosses below the longer-term MA, it's a sell signal
            elif buy and (df.iloc[-1, 1] > df.iloc[-1, 2]):
                print('Selling bitcoin')
                # tuple(bool: sold or not, sell price)
                sell_status_tuple = sell_bitcoin(bitcoin_amount, df.iloc[-1, 0])
                if sell_status_tuple[0]:
                    buy = False
        time.sleep(1)

if __name__ == '__main__':
    main()
