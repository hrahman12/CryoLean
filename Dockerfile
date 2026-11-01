# CryoLean API + website in one container: builds the Lean 4 checker from source, the SQLite catalog and the site,
# then serves them with `python -m cryolean serve`. Every verdict comes from the compiled Lean binary inside the image.
#   docker build -t cryolean .
#   docker run -p 8000:8000 cryolean        -> http://localhost:8000
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl git ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# Lean toolchain pinned by lean/lean-toolchain (elan installs exactly that version)
ENV ELAN_HOME=/opt/elan PATH=/opt/elan/bin:$PATH
RUN curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none

WORKDIR /app
COPY lean/ lean/
RUN cd lean && lake build cryolean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

COPY . .
RUN python -m cryolean build-db && python scripts/build_site.py

ENV HOST=0.0.0.0 PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "python -m cryolean serve --host $HOST --port $PORT"]
