import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel


def parse(text: str) -> List[Dict[str, Any]]:
    text = text.split(']')[1].strip()[:-1]
    kvs = text.split(',')
    kvs = [kv.strip() for kv in kvs]
    # kvs = {k.strip(): v.strip() for kv in kvs for k, v in kv.split(':')}
    new_kvs = {}
    for kv in kvs:
        k, v = kv.split(':')
        new_kvs[k.strip()] = v.strip()
    kvs = new_kvs

    metrics = [
        {
            "name": "Avg prompt throughput",
            "unit": "tokens/s",
            "value": None,
        }, {
            "name": "Avg generation throughput",
            "unit": "tokens/s",
            "value": None,
        }, {
            "name": "Running",
            "unit": "reqs",
            "value": None,
        }, {
            "name": "Swapped",
            "unit": "reqs",
            "value": None,
        }, {
            "name": "Pending",
            "unit": "reqs",
            "value": None,
        }, {
            "name": "GPU KV cache usage",
            "unit": "%",
            "value": None,
        }, {
            "name": "CPU KV cache usage",
            "unit": "%",
            "value": None
        }
    ]

    metrics_with_value = []
    for metric in metrics:
        name = metric["name"]
        unit = metric["unit"]
        metric_with_value = dict(metric)
        metric_with_value["value"] = kvs[name].split(unit)[0].strip()
        metrics_with_value.append(metric_with_value)
    return metrics_with_value


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(clear_server())
    yield


app = FastAPI(lifespan=lifespan)

vllm_servers = {}

data_lock = asyncio.Lock()


class LogData(BaseModel):
    server_name: str
    container_name: str
    log_content: str


async def clear_server():
    while True:
        async with data_lock:
            for server_name, data in vllm_servers.items():
                if time.time() - data["last_update"] > 10:
                    vllm_servers.pop(server_name)
        await asyncio.sleep(10)


@app.post("/api")
async def receive_log(log_data: LogData):
    try:
        parsed_data = parse(log_data.log_content)
    except Exception:
        return
    vllm_server = f"{log_data.server_name}_{log_data.container_name}"
    async with data_lock:
        vllm_servers[vllm_server] = {
            "log": parsed_data,
            "last_update": time.time()
        }
    return {"status": "ok"}


@app.get("/")
async def main():
    return vllm_servers


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9800)
