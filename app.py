import streamlit as st
import pandas as pd
import numpy as np
from nsetools import Nse
import nsepython as nsep        # library for NSE Option Chain
import sys
from load_css import local_css

st. set_page_config(layout="wide")
st.title = 'Option Strategy Planner'

indexes = ['NIFTY', 'BANNIFTY', 'FINNIFTY']

# Get all FnO items from NSE
@st.cache(allow_output_mutation=True)
def get_fno_items():
    nse = Nse()
    fno_items = nse.get_fno_lot_sizes()
    df = pd.DataFrame.from_dict(fno_items, orient='index')
    df.index.rename('symbol', inplace=True)
    return df

# Get the option chain from NSE using nsepython library
@st.cache(allow_output_mutation=True)
def fetch_oi_data(symbol,expiry="latest"):

    payload = nsep.nse_optionchain_scrapper(symbol)

    expiryDates = payload['records']['expiryDates']

    col_names = ['calls_oi','calls_oi_chng','calls_volume','calls_iv','calls_ltp','calls_net_chng','strikeprice','puts_oi','puts_oi_chng','puts_volume','puts_iv','puts_ltp','puts_net_chng']
    oi_data = pd.DataFrame(columns = col_names)

    oi_row = {'calls_oi':0,'calls_oi_chng':0,'calls_volume':0,'calls_iv':0,'calls_ltp':0,'calls_net_chng':0,'strikeprice':0,'puts_oi':0,'puts_oi_chng':0,'puts_volume':0,'puts_iv':0,'puts_ltp':0,'puts_net_chng':0}

    if(expiry=="latest"):
        expiry = payload['records']['expiryDates'][0]
    m=0
    for m in range(len(payload['records']['data'])):
        if(payload['records']['data'][m]['expiryDate']==expiry):
            if(1>0):
                try:
                    oi_row['calls_oi']=payload['records']['data'][m]['CE']['openInterest']
                    oi_row['calls_oi_chng']=payload['records']['data'][m]['CE']['changeinOpenInterest']
                    oi_row['calls_volume']=payload['records']['data'][m]['CE']['totalTradedVolume']
                    oi_row['calls_iv']=payload['records']['data'][m]['CE']['impliedVolatility']
                    oi_row['calls_ltp']=payload['records']['data'][m]['CE']['lastPrice']
                    oi_row['calls_net_chng']=payload['records']['data'][m]['CE']['change']
                except KeyError:
                    oi_row['calls_oi'], oi_row['callsoi_chng'], oi_row['calls_volume'], oi_row['calls_iv'], oi_row['calls_ltp'],oi_row['calls_net_chng']=0,0,0,0,0,0
                    pass

                oi_row['strikeprice']=payload['records']['data'][m]['strikePrice']

                try:
                    oi_row['puts_oi']=payload['records']['data'][m]['PE']['openInterest']
                    oi_row['puts_oi_chng']=payload['records']['data'][m]['PE']['changeinOpenInterest']
                    oi_row['puts_volume']=payload['records']['data'][m]['PE']['totalTradedVolume']
                    oi_row['puts_iv']=payload['records']['data'][m]['PE']['impliedVolatility']
                    oi_row['puts_ltp']=payload['records']['data'][m]['PE']['lastPrice']
                    oi_row['puts_net_chng']=payload['records']['data'][m]['PE']['change']
                except KeyError:
                    oi_row['puts_oi'], oi_row['puts_oi_chng'], oi_row['puts_Volume'], oi_row['puts_iv'], oi_row['puts_ltp'],oi_row['puts_Net Chng']=0,0,0,0,0,0
            else:
                logging.info(m)

            oi_data = oi_data.append(oi_row, ignore_index=True)

    return oi_data,float(payload['records']['underlyingValue']),payload['records']['timestamp'],expiryDates

# Read the option chain based on the selected symbol
@st.cache(allow_output_mutation=True)
def get_option_chain(symbol):
    
    #oi, ltp, dtime = nsep.oi_chain_builder(symbol)
    oi,ltp,dtime,expiry = fetch_oi_data(symbol)
    #oi = pd.DataFrame(oi, columns=['CALLS_OI', 'CALLS_Chng in OI', 'CALLS_IV', 'CALLS_LTP', 'Strike Price', 'PUTS_LTP', 'PUTS_IV', 'PUTS_OI', 'PUTS_Chng in OI'])
    #oi.rename(columns={'CALLS_OI':"call_oi", 'CALLS_Chng in OI': 'call_oi_chg', 'CALLS_IV':'call_iv', 'CALLS_LTP':'call_ltp', 'Strike Price':'strike', 'PUTS_LTP':'put_ltp', 'PUTS_IV':'put_iv', 'PUTS_OI':'put_oi', 'PUTS_Chng in OI':'put_oi_chg'}, inplace=True)

    # Remove the rows at the beginning and at the end (take only 15% up and down from LTP.. Strikes outside this are illiquid)
    strikefrom = 0.9 if symbol in indexes else 0.8
    striketo = 1.15 if symbol in indexes else 1.2
    strikefrom = strikefrom * ltp
    striketo = striketo * ltp

    oi = oi.loc[ (oi['strikeprice'] >= strikefrom) & (oi['strikeprice'] <= striketo) ]

    strikes = oi['strikeprice'].tolist()

    return oi, ltp, strikes


fno = get_fno_items()

inp, outp = st.beta_columns([1,6])

listSymbol = fno.index.tolist()
symbol = inp.selectbox('Symbol', listSymbol)


oi, ltp, strikes = get_option_chain(symbol)

#inp.write("LTP : %.2f" %(ltp))
local_css("style.css")
ltpf = f'{ltp:,.2f}'
txtout =  "<div>LTP: <span class='blue'>"+ltpf+"</span></div>"
inp.markdown(txtout, unsafe_allow_html=True)

lotSize = fno[symbol:symbol][0][0]
txtout = "<div>Lot size:  <span class='blue'>"+str(lotSize)+"</span></div>"
inp.markdown(txtout, unsafe_allow_html=True)
#inp.write('Lot size: '+str(lotSize))

optype = inp.radio('OpType', ("Call", "Put"))

trtype = inp.radio('Transaction', ("Buy", "Sell"))

lots = inp.slider("Lots", 0, 10, 1, 1)

strike = inp.selectbox('Strike Price', strikes)

oi.reset_index(inplace=True)
outp.write("Option Chain: ("+str(oi.shape[0])+" strikes)")
outp.dataframe(oi)

