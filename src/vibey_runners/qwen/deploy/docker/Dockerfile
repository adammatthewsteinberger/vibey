FROM python:3.12-slim AS build
WORKDIR /app
COPY . .
RUN pip wheel --no-deps --wheel-dir /wheels .

FROM python:3.12-slim
RUN useradd --create-home qwenloop
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl
USER qwenloop
ENTRYPOINT ["qwenloop"]

