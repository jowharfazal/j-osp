import streamlit as st
import pandas as pd
import numpy as np
from nsetools import Nse
import nsepython as nsep        # library for NSE Option Chain

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


# Read the option chain based on the selected symbol
@st.cache(allow_output_mutation=True)
def get_option_chain(symbol):
    
    oi, ltp, dtime = nsep.oi_chain_builder(symbol)
    oi = pd.DataFrame(oi, columns=['CALLS_OI', 'CALLS_Chng in OI', 'CALLS_IV', 'CALLS_LTP', 'Strike Price', 'PUTS_LTP', 'PUTS_IV', 'PUTS_OI', 'PUTS_Chng in OI'])
    oi.rename(columns={'CALLS_OI':"call_oi", 'CALLS_Chng in OI': 'call_oi_chg', 'CALLS_IV':'call_iv', 'CALLS_LTP':'call_ltp', 'Strike Price':'strike', 'PUTS_LTP':'put_ltp', 'PUTS_IV':'put_iv', 'PUTS_OI':'put_oi', 'PUTS_Chng in OI':'put_oi_chg'}, inplace=True)

    # Remove the rows at the beginning and at the end (take only 15% up and down from LTP.. Strikes outside this are illiquid)
    strikefrom = 0.9 if symbol in indexes else 0.8
    striketo = 1.15 if symbol in indexes else 1.2
    strikefrom = strikefrom * ltp
    striketo = striketo * ltp

    oi = oi.loc[ (oi['strike'] >= strikefrom) & (oi['strike'] <= striketo) ]

    strikes = oi['strike'].tolist()

    return oi, ltp, strikes


fno = get_fno_items()

inp, outp = st.beta_columns([1,7])

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

