FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=10000
WORKDIR /app
COPY pyproject.toml README.md ./
COPY commerceos ./commerceos
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 commerceos
USER commerceos
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/products/search?q=running', timeout=2); urllib.request.urlopen('http://127.0.0.1:' + os.environ['PORT'] + '/_stcore/health', timeout=2)"
CMD ["python", "-m", "commerceos.serve"]
