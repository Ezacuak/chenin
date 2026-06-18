import numpy as np
import pandas as pd
import streamlit as st

from report import Report

data = Report("./data/NOI_S/NOI_S_5.txt")


st.title("Chenin")

for k in data:
    st.header(k)
    st.write(data[k])
    st.space(size="small")
