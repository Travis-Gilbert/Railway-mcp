FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY railway_mcp/ ./railway_mcp/

RUN pip install --no-cache-dir .

# Railway injects PORT as an env var
ENV PORT=8000
ENV MCP_TRANSPORT=streamable-http

CMD ["python", "-m", "railway_mcp"]
