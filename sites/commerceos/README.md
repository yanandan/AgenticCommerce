# CommerceOS browser catalog

300 synthetic products organized into the requested categories: The Holiday Shop, Sports, Golf, Shoes, Women, Men, Kids, Accessories, Fan Shop, Exercise & Wellness, and Outdoor. Sports includes 50 products; each other category includes 25. Each item has one primary category and a specific product type. All brands, teams, products, and prices are fictional.

Search requires every query token and prioritizes names (5), categories/product types/sports (3), brands (2), then descriptions (1), with ID tie breaking. Includes category filtering, price/name sorting, and pagination. No checkout or persistent state.

Run `node check.mjs`. Hosted files are in `dist/`; the separate Streamlit/FastAPI project remains at the workspace root and uses the same catalog.

## Shopping chat

`chat.js` loads pinned Pyodide 0.27.7 and executes the exact shared Python parser and AND filtering core in `dist/python/commerceos/`. No JavaScript parser, LLM, or agents are used for chat requests. Browse-only keyword search remains in JavaScript. New requests are independent; history is display-only and session-local. Unknown requirements trigger refinement rather than partial matches. Width and marathon suitability are absent from the current catalog. Refresh shared Python assets from the repository root with `python scripts/sync_chat_python.py`; run `python scripts/sync_chat_python.py --check` to verify parity. See the root README for API flow, examples, and limitations.
