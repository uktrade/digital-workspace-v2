# Digital Workspace

A [Wagtail](https://www.wagtail.io)-based intranet for the Department for Business & Trade.

Project documentation is available [here](https://uktrade.github.io/digital-workspace-v2/).

# Setup DebugPy

Add environment variable in your .env file

    DEBUGPY_ENABLED=True

Create launch.json file inside .vscode directory

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Remote Attach (DebugPy)",
                "type": "debugpy",
                "request": "attach",
                "port": 5678,
                "host": "localhost",
                "pathMappings": [
                    {
                        "localRoot": "${workspaceFolder}",
                        "remoteRoot": "/app/"
                    }
                ],
                "justMyCode": true
            },
        ]
    }