"""Provider adapter contract. Replace respond() with a real model call.

The evaluator runs a new process for each episode. Preserve the received history
within this process. Do not inspect evaluator files, seeds, sibling runs or reports.
This template deliberately does not supply an automated scientific observer.
"""

import json
import sys


def respond(public_history, trial, answer_schema):
    raise NotImplementedError("Connect your model/provider here; return a DiscoveryAnswer dict")


def main():
    history, schema = [], None
    for line in sys.stdin:
        message = json.loads(line)
        if message["type"] == "start":
            history = message["history"]
            schema = message["answer_schema"]
        elif message["type"] == "trial":
            trial = message["trial"]
            answer = respond(history, trial, schema)
            print(json.dumps({"answer": answer}), flush=True)
            history.append({"trial": trial, "answer": answer})
        elif message["type"] == "complete":
            return


if __name__ == "__main__":
    main()
