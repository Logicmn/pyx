# PYX (Python Exchange)
# Created by Logicmn
# Started 11/19/16

#                               -----------------------------------------
#                               | Real-time stock trading program using |
#                               |   a basic mean reversion algorithm    |
#                               -----------------------------------------

#-------------------------------------Dependencies and database link-------------------------------------------
import datetime
from yahoo_finance import Share

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence, MetaData, create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///db2.db', echo=True) # Link the database to the SQLAlchemy engine
Session = sessionmaker(bind=engine)
Base = declarative_base()
metadata = MetaData()
session = Session()
#--------------------------------------------------------------------------------------------------------------

#-------------------------------------Creating tables for database--------------------------------------------
class Wallet(Base): # Create 'wallets' table
    __tablename__ = 'wallets'

    id = Column(Integer, Sequence('wallet_id_seq'), primary_key=True)
    name = Column(String)
    balance = Column(Integer)

    def __repr__(self):
        return "<Wallet(name='%s', balance='%s')>" % (self.name, self.balance)

class Transaction(Base): # Create 'transactions' table
    __tablename__ = 'transactions'

    id = Column(Integer, Sequence('transaction_id_seq'), primary_key=True)
    stock = Column(String(50))
    symbol = Column(String(50))
    buy_or_sell = Column(String(50))
    price = Column(Integer())
    ema = Column(Integer())
    shares = Column(Integer())
    time = Column(String(50))

    def __repr__(self):
        return "<Transaction(stock='%s', symbol='%s', buy_or_sell='%s', price='%s', ema='%s', shares='%s', time='%s')>"\
               % (self.stock, self.symbol, self.buy_or_sell, self.price, self.ema, self.shares, self.time)
#--------------------------------------------------------------------------------------------------------------

#----------------------------------------Creating mean reversion algorithm-------------------------------------
class Strategy(object): # Create the algorithm PYX will use to trade with
    def __init__(self, equity):
        self.equity = equity

    def getEquity(self):
        return self.equity

    def calcEMA(self, closePrice, prevEMA): # Calculate the exponential moving average
        multiplier = 2 / (50 + 1)
        EMA = (closePrice - prevEMA) * multiplier + prevEMA
        return EMA

    def calcUpper(self, EMA): # Calculate the upper Bollinger band
        upperBand = EMA * (1 + .02)
        return upperBand

    def calcLower(self, EMA): # Calculate the lower Bollinger band
        lowerBand = EMA * (1 - .02)
        return lowerBand
#--------------------------------------------------------------------------------------------------------------

#------------------------------------------Buy/sell shares of a stock------------------------------------------
def enter_position(mean_reversion, apple): # Buy shares of a stock
    closePrice = float(apple.get_prev_close())
    prevEMA = float(apple.get_50day_moving_avg())
    EMA = mean_reversion.calcEMA(closePrice, prevEMA)
    lowerBand = float(mean_reversion.calcLower(EMA))
    purchase_query = session.query(Transaction.buy_or_sell).order_by(Transaction.id.desc()).first() # Find out whether the latest purchase was a buy/sell
    if purchase_query != None:
        purchase = purchase_query[0]
    else:
        purchase = 'sell'
    if float(apple.get_price()) <= lowerBand and purchase != 'buy': # Buy shares if the last purchase was a sell
        print('buy')
        new_transaction = Transaction(stock='Apple', symbol=apple.get_info()['symbol'], buy_or_sell='buy',
                                      price=apple.get_price(),
                                      ema=EMA, shares='100', time=datetime.datetime.now())
        session.add(new_transaction)
        session.commit()
        new_price = session.query(Transaction.price).order_by(Transaction.id.desc()).first()
        new_shares = session.query(Transaction.shares).order_by(Transaction.id.desc()).first()
        new_funds = new_price[0] * new_shares[0]
        balance = session.query(Wallet.balance).one()
        current_bal = session.query(Wallet).one()
        session.delete(current_bal)
        session.commit()
        new_bal = balance[0] - new_funds # Subtract amount spent from the balance in wallet
        primary_wallet = Wallet(name='Primary Wallet', balance=new_bal)
        session.add(primary_wallet)
        session.commit()


def exit_position(mean_reversion, apple): # Sell shares of a stock
    closePrice = float(apple.get_prev_close())
    prevEMA = float(apple.get_50day_moving_avg())
    EMA = mean_reversion.calcEMA(closePrice, prevEMA)
    upperBand = float(mean_reversion.calcUpper(EMA))
    purchase_query = session.query(Transaction.buy_or_sell).order_by(Transaction.id.desc()).first() # Find out whether the latest purchase was a buy/sell
    if purchase_query != None:
        purchase = purchase_query[0]
    else:
        purchase = 'buy'
    if float(apple.get_price()) >= upperBand and purchase != 'sell': # Sell shares if the last purchase was a buy
        print('sell')
        new_transaction = Transaction(stock='Apple', symbol=apple.get_info()['symbol'], buy_or_sell='sell',
                                      price=apple.get_price(),
                                      ema=EMA, shares='100', time=datetime.datetime.now())
        session.add(new_transaction)
        session.commit()
        new_price = session.query(Transaction.price).order_by(Transaction.id.desc()).first()
        new_shares = session.query(Transaction.shares).order_by(Transaction.id.desc()).first()
        new_funds = new_price[0] * new_shares[0]
        balance = session.query(Wallet.balance).one()
        current_bal = session.query(Wallet).one()
        session.delete(current_bal)
        session.commit()
        new_bal = balance[0] + new_funds # Add amount gained to the balance in wallet
        primary_wallet = Wallet(name='Primary Wallet', balance=new_bal)
        session.add(primary_wallet)
        session.commit()
#--------------------------------------------------------------------------------------------------------------

#-------------------------------------------------Main function------------------------------------------------
def main():
    apple = Share('AAPL') # Which stock to monitor and invest in
    Base.metadata.create_all(engine)
    session.commit()
    b = session.query(Wallet.balance).first() # Check if there is already a wallet
    if b == None:
        primary_wallet = Wallet(name='Primary Wallet', balance=100000) # Create the wallet with a balance of $100,000
        session.add(primary_wallet)
        session.commit()
    mean_reversion = Strategy(apple.get_info()['symbol']) # Run the EMA, and Bollinger band calculations
    enter_position(mean_reversion, apple) # Buy stock if applicable
    exit_position(mean_reversion, apple) # Sell stock if applicable
    session.commit()
#--------------------------------------------------------------------------------------------------------------

main()
