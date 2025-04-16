import * as Sentry from "@sentry/browser";

/**
 * Return config from meta html elements.
 * @param {string} name - The end part of the meta name attribute.
 * @returns {(string|undefined)}
 */
function config(name) {
  return document.querySelector(`meta[name="intranet:${name}"]`)?.content;
}

function sentryInit() {
  const dsn = config("sentry:dsn");

  if (!dsn) {
    console.log("Ignore sentry (no DSN provided)");
    return;
  }

  console.log("Initialise sentry");

  Sentry.init({
    dsn,
    release: config("release"),
    environment: config("environment"),
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: Number(config("sentry:browser-traces-sample-rate")),
  });
}

sentryInit();
