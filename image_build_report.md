# Environment Secrets Store Image Build Report

## Build Environment

- Base image: `python:3.12.9-slim`
- Dockerfile: `Dockerfile.dev`
- Image tag: `environment-secrets-store:dev`
- Additional dependency required: No

## Build Command

```powershell
docker build -f Dockerfile.dev -t environment-secrets-store:dev .
```

The Docker image was built successfully.

## Runtime Environment Variable Test

The container was started with a runtime environment variable:

```powershell
docker run --rm --entrypoint python `
  -e TEST_SECRET=demo-secret `
  environment-secrets-store:dev `
  -c "import os; print(os.getenv('TEST_SECRET'))"
```

Output:

```text
demo-secret
```

The same container was then started without providing the environment variable.

Output:

```text
None
```

## Result

The environment variable can be passed to the container at runtime and is not
embedded directly into the Docker image.

A `.dockerignore` file was also added to prevent `.env` files and other
unnecessary files from being copied into the image.