import streamlit as st

st.title("Hello World!")
st.write("Questa è una app Streamlit super semplice")
st.success("Se vedi questo, Streamlit funziona!")

if st.button("Clicca qui"):
    st.balloons()
    st.write("Bottone cliccato!")
