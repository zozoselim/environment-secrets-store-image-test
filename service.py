
import os
import sys
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from sdks.novavision.src.base.request import Request as SDKRequest
from sdks.novavision.src.base.service import Service, run_executor
from sdks.novavision.src.base.bootstrap import Bootstrap
from sdks.novavision.src.base.auth import api_key_security
from sdks.novavision.src.helper.service import start_server, terminate_processes_and_cleanup


terminate_processes_and_cleanup(path="/storage/runtime/package", folderName="package")

bootstrap = {}
@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap["bootstrap"] = Bootstrap().run()
    yield

app = FastAPI(lifespan=lifespan)


def _service_status():
    if "bootstrap" in bootstrap:
        return {"status": "open", "message": "Service is opened successfully"}
    return {"status": "loading", "message": "Server is still in the loading phase"}


def _is_direct_package_request(request_json: dict):
    return (
        isinstance(request_json, dict)
        and "mode" not in request_json
        and request_json.get("name")
        and isinstance(request_json.get("configs"), dict)
        and isinstance(request_json["configs"].get("executor"), dict)
    )


async def _run_direct_package_request(request_json: dict):
    try:
        package_name = request_json["name"]
        executor_name = request_json["configs"]["executor"]["value"]["name"]
        loaded = bootstrap["bootstrap"]
        executor_bootstrap = loaded[package_name][executor_name]
        executor_module = loaded["executors"][package_name][executor_name]
        executor_class = getattr(executor_module, executor_name)

        return run_executor(
            request=SDKRequest(request_json),
            bootstrap=executor_bootstrap,
            from_executor=executor_class,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Direct package execution failed.",
        )


@app.get('/')
@app.get('/api')
async def root():
    return {
        **_service_status(),
        "routes": {
            "status": "/status",
            "api": "/api",
        },
    }


@app.post('/status')
async def status(access_token: str = Depends(api_key_security)):
    return _service_status()


@app.post('/')
@app.post('/api')
async def api(request: Request, access_token: str = Depends(api_key_security)):
    request_json = await request.json()
    if _is_direct_package_request(request_json):
        return await _run_direct_package_request(request_json)

    json_data = json.dumps(request_json)
    resp = await Service(data=json_data, load=bootstrap['bootstrap']).run()
    return resp


if __name__ == "__main__":
    start_server(app=app)
