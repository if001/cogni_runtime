from __future__ import annotations

import argparse

from cogni_runtime.worker_runtime import TaskAdapter, AdapterRegistry, ZmqWorker


class SampleAgentAdapter(TaskAdapter):
    kind = "sample_agent"

    def __init__(self):
        pass

    def run(self, payload):
        message = payload.get("message", "")

        print(f"[adapter] message from agent :{message}")

        ## ダミー
        # app = self.build_graph()
        # result = app.invoke({"theme": theme})
        # result = await app.ainvoke({"theme": theme})
        result = {"final_text": f"sample_agent completed research on '{message}'"}

        return {
            "message": result,
        }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--name",
        required=True,
        help="worker name (worker1, worker2, etc)",
    )

    parser.add_argument(
        "--connect",
        default="tcp://127.0.0.1:5555",
        help="controller address",
    )

    args = parser.parse_args()

    registry = AdapterRegistry()

    registry.register(SampleAgentAdapter())

    worker = ZmqWorker(
        worker_name=args.name,
        connect_addr=args.connect,
        registry=registry,
    )
    print("start sample worker")
    worker.serve_forever()


if __name__ == "__main__":
    main()
