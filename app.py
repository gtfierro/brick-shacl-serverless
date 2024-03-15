# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import signal
import sys
from types import FrameType
from rdflib import Graph

from flask import Flask, request, jsonify
import ontoenv

from utils.logging import logger
from brick_tq_shacl.topquadrant_shacl import validate, infer

app = Flask(__name__)

env = ontoenv.OntoEnv()

s = Graph()
s.parse("https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl", format="ttl")
env.import_dependencies(s)

@app.route("/")
def hello() -> str:
    # Use basic logging with custom fields
    logger.info(logField="custom-entry", arbitraryField="custom-entry")

    # https://cloud.google.com/run/docs/logging#correlate-logs
    logger.info("Child logger with trace Id.")

    return "Hello, World!"

# FLASK handler which accepts a POST request with a JSON payload
@app.route("/validate", methods=["POST"])
def validate_graph() -> str:
    body = request.json
    # data graph
    data = Graph()
    data.parse(data=body['data'], format="json-ld")

    # validate the data graph against the SHACL graph
    valid, report_g, report_str = validate(data, s)
    # return JSON response
    return jsonify({"valid": valid, "report": report_g.serialize(format="json-ld")})

def shutdown_handler(signal_int: int, frame: FrameType) -> None:
    logger.info(f"Caught Signal {signal.strsignal(signal_int)}")

    from utils.logging import flush

    flush()

    # Safely exit program
    sys.exit(0)


if __name__ == "__main__":
    # Running application locally, outside of a Google Cloud Environment

    # handles Ctrl-C termination
    signal.signal(signal.SIGINT, shutdown_handler)

    app.run(host="localhost", port=8080, debug=True)
else:
    # handles Cloud Run container termination
    signal.signal(signal.SIGTERM, shutdown_handler)
