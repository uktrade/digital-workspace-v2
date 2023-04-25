FROM digital_workspace/wagtail:latest

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN adduser pwuser

RUN poetry run playwright install-deps
RUN poetry run playwright install

COPY . ./
