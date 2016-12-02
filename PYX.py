# PYX (Python Exchange)
# Created by Logicmn
# 11/19/16

#          -----------------------------------------
#          | Real-time stock trading program using |
#          |   a basic mean reversion algorithm    |
#          -----------------------------------------

#--------------------------------------------------------------------------------------------------------------
import datetime
from yahoo_finance import Share

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence, MetaData, create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///db1.db', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()
metadata = MetaData()
session = Session()

#--------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------
class Wallet(Base):
    __tablename__ = 'wallets'

    id = Column(Integer, Sequence('wallet_id_seq'), primary_key=True)
    name = Column(String)
    balance = Column(Integer)

    def __repr__(self):
        return "<Wallet(name='%s', balance='%s')>" % (self.name, self.balance)

class Transaction(Base):
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
        return "<Transaction(stock='%s', symbol='%s', buy_or_sell='%s', price='%s', ema='%s', shares='%s', time='%s')>" % (self.stock, self.symbol, self.buy_or_sell, self.price, self.ema, self.shares, self.time)
#--------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------
class Strategy(object):
    def __init__(self, equity):
        self.equity = equity

    def getEquity(self):
        return self.equity

    def calcEMA(self, closePrice, prevEMA):
        multiplier = 2 / (50 + 1)
        EMA = (closePrice - prevEMA) * multiplier + prevEMA
        return EMA

    def calcUpper(self, EMA):
        upperBand = EMA * (1 + .04)
        return upperBand

    def calcLower(self, EMA):
        lowerBand = EMA * (1 - .04)
        return lowerBand
#--------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------
def enter_position(mean_reversion, apple):
    closePrice = float(apple.get_prev_close())
    prevEMA = float(apple.get_50day_moving_avg())
    EMA = mean_reversion.calcEMA(closePrice, prevEMA)
    lowerBand = float(mean_reversion.calcLower(EMA))
    purchase_query = session.query(Transaction.buy_or_sell).order_by(Transaction.id.desc()).first()
    if purchase_query != None:
        purchase = purchase_query[0]
    else:
        purchase = 'sell'
    print('------')
    print(apple.get_price(), lowerBand)
    print('------')
    if float(apple.get_price()) <= lowerBand and purchase != 'buy':
        print('buy')
        new_transaction = Transaction(stock='Apple', symbol=apple.get_info()['symbol'], buy_or_sell='buy',
                                      price=apple.get_price(),
                                      ema=EMA, shares='100', time=datetime.datetime.now())
        session.add(new_transaction)
        session.commit()
        new_funds = Transaction.price * Transaction.shares
        Wallet.balance -= new_funds
        session.commit()

def exit_position(mean_reversion, apple):
    closePrice = float(apple.get_prev_close())
    prevEMA = float(apple.get_50day_moving_avg())
    EMA = mean_reversion.calcEMA(closePrice, prevEMA)
    upperBand = float(mean_reversion.calcUpper(EMA))
    purchase_query = session.query(Transaction.buy_or_sell).order_by(Transaction.id.desc()).first()
    if purchase_query != None:
        purchase = purchase_query[0]
    else:
        purchase = 'buy'
    print('------')
    print(apple.get_price(), upperBand)
    print('------')
    if float(apple.get_price()) >= upperBand and purchase != 'sell':
        print('sell')
        new_transaction = Transaction(stock='Apple', symbol=apple.get_info()['symbol'], buy_or_sell='sell',
                                      price=apple.get_price(),
                                      ema=EMA, shares='100', time=datetime.datetime.now())
        session.add(new_transaction)
        session.commit()
        new_funds = Transaction.price * Transaction.shares
        Wallet.balance += new_funds
        session.commit()
#--------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------
def main():
    apple = Share('AAPL')
    Base.metadata.create_all(engine)
    session.commit()
    b = session.query(Wallet.balance).first()
    if b == None:
        primary_wallet = Wallet(name='Primary Wallet', balance=100000)
        session.add(primary_wallet)
        session.commit()
    print(session.query(Wallet.balance).first(), 'hi')
    mean_reversion = Strategy(apple.get_info()['symbol'])
    enter_position(mean_reversion, apple)
    exit_position(mean_reversion, apple)
    session.commit()
#--------------------------------------------------------------------------------------------------------------

main()
