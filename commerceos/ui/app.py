import os

import httpx
import streamlit as st

API_URL = os.getenv('COMMERCEOS_API_URL', 'http://127.0.0.1:8000').rstrip('/')
CATEGORIES = ['The Holiday Shop', 'Sports', 'Golf', 'Shoes', 'Women', 'Men', 'Kids',
              'Accessories', 'Fan Shop', 'Exercise & Wellness', 'Outdoor']
EXAMPLES = ['Show me running shoes under $150',
            'I need wide running shoes for marathon training',
            'Find hiking products under $100']

st.set_page_config(page_title='CommerceOS', page_icon='🏀', layout='wide')
st.title('CommerceOS')
st.caption('300 fictional products. Deterministic shopping requests. Illustrative USD prices.')


def product_cards(products, limit=None):
    columns = st.columns(3)
    for index, product in enumerate(products if limit is None else products[:limit]):
        with columns[index % 3]:
            with st.container(border=True):
                st.subheader(product['name'])
                st.caption(f"{product['category']} · {product['sport']}")
                st.write(product['description'])
                st.markdown(f"**${product['price_cents'] / 100:,.2f}**")
                st.caption(product['id'])
    if limit is not None and len(products) > limit:
        st.caption(f'Showing the first {limit} of {len(products)} matches. Add requirements to narrow your request.')


def shopping_reply(result):
    st.markdown('**Requirements recognized**')
    if result['recognized']:
        for requirement in result['recognized']:
            st.write(f'• {requirement}')
    else:
        st.write('None yet.')
    for requirement in result['unverified_requirements']:
        st.warning(requirement)
    if result['status'] == 'needs_refinement':
        st.info('Please refine your request. No products are presented as confirmed matches.')
        for note in result['clarifications']:
            st.write(note)
    elif result['total']:
        st.success(f"{result['total']} products match every recognized requirement.")
        product_cards(result['products'], limit=12)
    else:
        st.info('No products match every requirement. No filters were relaxed. Try a different complete request.')
    with st.expander('Request → result data flow'):
        st.write('Your message → Python phrase and price rules → recognized constraints → shared catalog filters (AND) → results.')
        st.json({'request': result['message'], 'constraints': result['constraints'],
                 'unverified_requirements': result['unverified_requirements'],
                 'status': result['status'], 'matching_product_ids': [p['id'] for p in result['products']]})


chat, browse = st.tabs(['Shopping chat', 'Browse catalog'])
with chat:
    st.subheader('Tell us what you’re shopping for')
    st.caption('Each message is a new, complete request. Requirements do not carry between messages. Chat history is only displayed in this session.')
    st.caption('Width is not recorded in this catalog. Use cases require explicit catalog wording; suitability is not inferred.')
    st.session_state.setdefault('shopping_messages', [])
    pending = None
    for column, example in zip(st.columns(3), EXAMPLES):
        if column.button(example, use_container_width=True):
            pending = example
    if st.button('Clear conversation'):
        st.session_state.shopping_messages = []
        st.rerun()
    for entry in st.session_state.shopping_messages:
        with st.chat_message(entry['role']):
            if 'result' in entry:
                shopping_reply(entry['result'])
            else:
                st.write(entry['content'])
    typed = st.chat_input('For example: Show me running shoes under $150', max_chars=500)
    message = pending or typed
    if message:
        st.session_state.shopping_messages.append({'role': 'user', 'content': message})
        with st.chat_message('user'):
            st.write(message)
        with st.chat_message('assistant'):
            try:
                response = httpx.post(f'{API_URL}/shopping/requests', json={'message': message}, timeout=15)
                response.raise_for_status()
                result = response.json()
            except (httpx.HTTPError, ValueError):
                content = 'Shopping search is unavailable. Check that the FastAPI server is running and try again.'
                st.error(content)
                st.session_state.shopping_messages.append({'role': 'assistant', 'content': content})
            else:
                shopping_reply(result)
                st.session_state.shopping_messages.append({'role': 'assistant', 'result': result})

with browse:
    category = st.selectbox('Category', ['All categories', *CATEGORIES])
    with st.form('search'):
        query = st.text_input('Search sports products', placeholder='Try basketball, running shoes, or yoga', max_chars=200)
        st.form_submit_button('Search')
    try:
        response = httpx.get(f'{API_URL}/products/search', params={
            'q': query, 'category': '' if category == 'All categories' else category}, timeout=10)
        response.raise_for_status()
        results = response.json()
    except (httpx.HTTPError, ValueError):
        st.error('Search is unavailable. Check that the FastAPI server is running and try again.')
    else:
        st.write(f"{results['total']} products found")
        if not results['products']:
            st.info('No matching products. Try a sport or a broader product name.')
        product_cards(results['products'])
