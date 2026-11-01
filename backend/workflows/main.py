"""Entry point for the Render Workflow service.

Start command (Render dashboard):  render-workflows workflows.main:app
Run from the backend/ directory (the service root directory), after `pip install -r requirements.txt`.
"""

import logging

from workflows.registry import app

# Importing the task modules registers their tasks on `app`.
from workflows.tasks import pipeline  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

if __name__ == "__main__":
    app.start()
