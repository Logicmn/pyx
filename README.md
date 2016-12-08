# PYX (Python Exchange)
*A program that simulates real-time stock trading using a basic mean reversion algorithm.*

**What is PYX?**
---------------------------------
PYX is a flexible program that simulates the trading of equity using different algorthms. The algorthm currently being used is a [mean reversion](http://www.investopedia.com/terms/m/meanreversion.asp?lgl=no-infinite) strategy. PYX buys and sells shares of stock based on the price compared to its upper and lower bollinger bands.

**What this program does:**

1. Creates a database ([SQLAlchemy](http://www.sqlalchemy.org/)) for storing each transaction and wallet
2. Creates a wallet from which simulated funds will be added to and subtracted from
3. Calculates the 50 day [exponential moving average](http://www.investopedia.com/terms/e/ema.asp?lgl=no-infinite) for specified stock
4. Calculates the upper and lower bollinger bands based on the 50 day EMA
5. Checks if the price of specified stock is `>=` or `<=` the upper and lower bollinger bands respectively
6. If the share price is `<=` the lower bollinger band, the program will buy shares
7. If the share price is `=>` the upper bollinger band, the program will sell previously bought shares
8. Each transaction is logged in a database `transaction_database.db` with the following information: `id|stock|symbol|buy/sell|price|ema|shares|date`

**How does it work?**
---------------------------------

**Dependencies:**

PYX relies on two main dependencies, `yahoo_finance` and `sqlalchemy`. PYX also utilizes Python 3.5's built in `datetime` module.

To install these modules with PyPI, first install [pip](https://pip.pypa.io/en/stable/installing/) then in cmd or bash run:
`pip install yahoo_finance`
`pip install sqlalchemy`
Once the packages have unpacked and installed, the program is good to run.

**Calculations:**

Equation to calculate the 50 day EMA:
```
multiplier = 2 / (50 + 1)
EMA = (closePrice - prevEMA) * multiplier + prevEMA
```
Equation to calculate upper bollinger band:
`upperBand = EMA * (1 + .02)`
Equation to calculate the lower bollinger band:
`lowerBand = EMA * (1 - .02)`

Adjust the `.02` to raise and lower the bollinger bands. The higher you raise the number to, the less likely it will be stock will be bought.

**Database:**

A database with two tables is created on the first initialization of the program, `wallets` and `transactions`. If there is no database transactions_database.db already, one will be created. A wallet containing a name and a balance will also be created and inserted into `wallets` the first time the program is run. To change the wallets balance simply edit `balance='100000'` in the `main()` function.

Everytime shares of a stock are bought and sold a row is added to the `transactions` database, code below.
```
new_transaction = Transaction(stock='Apple', symbol=apple.get_info()['symbol'], buy_or_sell='',
                              price=apple.get_price(),
                              ema=EMA, shares='100', time=datetime.datetime.now())
session.add(new_transaction)
session.commit()
```
To adjust the number of shares being bought, change the `shares='100'` to however many shares you want the program to buy.

**DISCLAIMER**
---------------------------------
*This program does not spend real money, nor does it buy real shares of stocks. It is simply a simulation.*
