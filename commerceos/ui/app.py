import os

import httpx
import streamlit as st

API_URL = os.getenv('COMMERCEOS_API_URL', 'http://127.0.0.1:8000').rstrip('/')

st.set_page_config(page_title='CommerceOS', page_icon='🏀', layout='wide')
st.title('CommerceOS')
st.caption('Explore 300 fictional sports products. All prices are synthetic USD examples.')

CATEGORIES = ['The Holiday Shop', 'Sports', 'Golf', 'Shoes', 'Women', 'Men', 'Kids',
              'Accessories', 'Fan Shop', 'Exercise & Wellness', 'Outdoor']
category = st.selectbox('Category', ['All categories', *CATEGORIES])

with st.form('search'):
    query = st.text_input('Search sports products', placeholder='Try basketball, running shoes, or yoga', max_chars=200)
    st.form_submit_button('Search')

try:
    response = httpx.get(f'{API_URL}/products/search', params={'q': query, 'category': '' if category == 'All categories' else category}, timeout=10)
    response.raise_for_status()
    results = response.json()
except (httpx.HTTPError, ValueError):
    st.error('Search is unavailable. Check that the FastAPI server is running and try again.')
    st.stop()

st.write(f"{results['total']} products found")
if not results['products']:
    st.info('No matching products. Try a sport or a broader product name.')
else:
    columns = st.columns(3)
    for index, product in enumerate(results['products']):
        with columns[index % 3]:
            with st.container(border=True):
                st.subheader(product['name'])
                st.caption(f"{product['category']} · {product['sport']}")
                st.write(product['description'])
                st.markdown(f"**${product['price_cents'] / 100:,.2f}**")
                st.caption(product['id'])
