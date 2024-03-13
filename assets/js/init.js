import * as Sentry from "@sentry/browser";

function config(name) {
  const meta = document.querySelector(`meta[name="intranet:${name}"]`);

  return meta !== null ? meta.content : null;
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
  });
}

sentryInit();
