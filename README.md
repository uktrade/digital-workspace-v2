# Digital Workspace

A [Wagtail](https://www.wagtail.io)-based intranet for the Department for Business & Trade.

Project documentation is available [here](https://uktrade.github.io/digital-workspace-v2/).

# Setup DebugPy

Add environment variable in your .evn file

    ENABLE_DEBUGPY=True

Enable port for debugpy in docker compose file

    ports:
      - "5678:5678"
