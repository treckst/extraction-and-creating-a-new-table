from traceback import print_tb
import psycopg2
import sqlalchemy as sa
import requests
import pandas as pd
from sqlalchemy.types import String, Numeric, Date
from sqlalchemy import create_engine, MetaData, Table, Column

# a function which extracts PLN rates for each currency
def check_rates(table):

    response = requests.get(f'https://api.nbp.pl/api/exchangerates/tables/{table}')
    data = response.json()[0]
    df = pd.DataFrame(data['rates'])
    df['rates_date'] = data['effectiveDate']
    df_ind = df.set_index("code").sort_values(['mid'], ascending=False).rename(columns={'mid':'mid_pln'})
    return df_ind
  
# a function which extracts a price of Gold(1mg) in PLN
def check_gold():
    url = 'https://api.nbp.pl/api/cenyzlota'
    response = requests.get(url)
    gold = response.json()
    dfgold = pd.DataFrame(gold)
    return dfgold
  
#Creating the connection with a postgresql database (deployed in Azure)(hidden username and password)
engine = sa.create_engine('postgresql://REDACTED:REDACRED.postgres.database.azure.com/postgres')
with engine.connect() as connection:

  #creating a new table and defining the kind of value a variable can hold
  
    metadata = MetaData()
    gold_table = Table(
        'gold_conversion_rates', metadata,
        Column('code', String(3), primary_key=True),
        Column('currency', String(100)),
        Column('mid_pln', Numeric(10, 2)),
        Column('rates_date', Date()),
        Column('1mg_gold_price', Numeric(10, 2)),
    )

  #inserting into a new table 
    rates_df = check_rates("A")
    gold_df = check_gold()
    current_gold_pln = gold_df.iloc[0]['cena']
  # calculating a gold price in each currency
    rates_df['1mg_gold_price'] = current_gold_pln / rates_df['mid_pln']
    rates_df['1mg_gold_price'] = rates_df['1mg_gold_price'].round(2)
    rates_df.to_sql(
        name = "gold_conversion_rates",
        con = engine,
        schema = "public",
        index = True,
        index_label = "code",
        if_exists = 'append',)


