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

engine = create_engine('sqlite:///new_db.db', echo=True) # Link the database to the SQLAlchemy engine
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

    def calcEMA(self, close_price, prev_ema): # Calculate the exponential moving average
        multiplier = 2 / (50 + 1)
        ema = (close_price - prev_ema) * multiplier + prev_ema
        return ema

    def calcUpper(self, ema): # Calculate the upper Bollinger band
        upper_band = ema * (1 + .02)
        return upper_band

    def calcLower(self, ema): # Calculate the lower Bollinger band
        lower_band = ema * (1 - .02)
        return lower_band
#--------------------------------------------------------------------------------------------------------------

#------------------------------------------Buy/sell shares of a stock------------------------------------------
def enter_position(mean_reversion, stock): # Buy shares of a stock
    close_price, prev_ema, ema, lower_band, upper_band, purchase_query = calculations(mean_reversion, stock)
    if purchase_query != None:
        purchase = purchase_query[0]
    else:
        purchase = 'sell'
    if float(stock.get_price()) <= lower_band and purchase != 'buy': # Buy shares if the last purchase was a sell
        print('buy')
        new_transaction = Transaction(stock=stock.get_name(), symbol=stock.symbol, buy_or_sell='buy',
                                      price=stock.get_price(),
                                      ema=ema, shares='100', time=datetime.datetime.now())
        session.add(new_transaction)
        session.commit()
        balance, new_funds = calc_wallet()
        new_bal = balance[0] - new_funds # Subtract amount spent from the balance in wallet
        primary_wallet = Wallet(name='Primary Wallet', balance=new_bal) # Re-create wallet with new balance
        session.add(primary_wallet)
        session.commit()


def exit_position(mean_reversion, stock): # Sell shares of a stock
    close_price, prev_ema, ema, lower_band, upper_band, purchase_query = calculations(mean_reversion, stock)
    if purchase_query != None:
        purchase = purchase_query[0]
    else:
        purchase = 'buy'
    if float(stock.get_price()) >= upper_band and purchase != 'sell': # Sell shares if the last purchase was a buy
        print('sell')
        new_transaction = Transaction(stock=stock.get_name(), symbol=stock.symbol, buy_or_sell='sell',
                                      price=stock.get_price(),
                                      ema=ema, shares='100', time=datetime.datetime.now())
        session.add(new_transaction)
        session.commit()
        balance, new_funds = calc_wallet()
        new_bal = balance[0] + new_funds # Add amount gained to the balance in wallet
        primary_wallet = Wallet(name='Primary Wallet', balance=new_bal) # Re-create wallet with new balance
        session.add(primary_wallet)
        session.commit()
#--------------------------------------------------------------------------------------------------------------

#-------------------------------------------------Calculations-------------------------------------------------
def calculations(mean_reversion, stock):
    close_price = float(stock.get_prev_close())# Calculate yesterdays close price
    prev_ema = float(stock.get_50day_moving_avg()) # Calculate the previous EMA
    ema = mean_reversion.calcEMA(close_price, prev_ema) # Calculate the EMA
    lower_band, upper_band= float(mean_reversion.calcLower(ema)), float(mean_reversion.calcUpper(ema)) # Calculate the bands
    print("-------------------------")
    purchase_query = session.query(Transaction.buy_or_sell).order_by(
                     Transaction.id.desc()).first()  # Find out whether the latest purchase was a buy/sell
    return close_price, prev_ema, ema, lower_band, upper_band, purchase_query

def calc_wallet():
    new_price = session.query(Transaction.price).order_by(Transaction.id.desc()).first() # Grab the bought price
    new_shares = session.query(Transaction.shares).order_by(Transaction.id.desc()).first() # Grab how many shares were bought
    new_funds = new_price[0] * new_shares[0] # Calculate the money spent
    balance = session.query(Wallet.balance).one() # Grab the current balance
    current_bal = session.query(Wallet).one()
    session.delete(current_bal) # Delete the wallet
    session.commit()
    return balance, new_funds
#--------------------------------------------------------------------------------------------------------------

#-------------------------------------------------Main function------------------------------------------------
def main():
    symbol = 'AAPL'  # Which stock to monitor and invest in
    stock = Share(symbol)
    if stock.get_price() is None:
        print("Error : {} has no price history".format(symbol))
        exit(1)
    print(stock.get_price())
    Base.metadata.create_all(engine)
    session.commit()
    b = session.query(Wallet.balance).first() # Check if there is already a wallet
    if b == None:
        primary_wallet = Wallet(name='Primary Wallet', balance=100000) # Create the wallet with a balance of $100,000
        session.add(primary_wallet)
        session.commit()
    mean_reversion = Strategy(symbol) # Run the EMA, and Bollinger band calculations
    enter_position(mean_reversion, stock) # Buy stock if applicable
    exit_position(mean_reversion, stock) # Sell stock if applicable
    session.commit()
#--------------------------------------------------------------------------------------------------------------

#----Runs the program-----
if __name__ == "__main__":
    main()
#-------------------------
