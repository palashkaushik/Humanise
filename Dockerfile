FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv pip install --system .[all]
COPY humanise/ ./humanise/
EXPOSE 8000
CMD ["uvicorn", "humanise.web:app", "--host", "0.0.0.0", "--port", "8000"]
