# Step-by-Step Guide: Installing the Trainium AI Piece

Follow these instructions to add the custom AI piece to your local ActivePieces instance.

## 1. Create the Piece Folder

On your host machine, ensure the following directory structure exists:

```bash
/Users/timtrainor/PycharmProjects/career-trainium/activepieces-pieces/trainium-ai/
```

I have already created the `index.ts` and `package.json` files in this location for you.

## 2. Enable Local Pieces in ActivePieces

To make ActivePieces see your local folders as pieces, you have two options:

### Option A: The CLI Method (Recommended for Development)

1. **Install the CLI**: `npm install -g @activepieces/cli`
2. **Login**: `ap login --host http://localhost:8280`
3. **Publish**:

    ```bash
    cd /Users/timtrainor/PycharmProjects/career-trainium/activepieces-pieces/trainium-ai
    ap pieces publish
    ```

### Option B: The Docker Mount Method (Advanced)

If you prefer not to use the CLI, you can mount your local folder directly into the ActivePieces container.

1. **Update `docker-compose.yml`**:

    ```yaml
    activepieces:
      ...
      volumes:
        - ./activepieces-pieces:/usr/src/app/packages/pieces/local
    ```

2. **Restart**: `docker compose up -d activepieces`

## 3. Configure the Piece in the UI

1. **Open ActivePieces**: Go to `http://localhost:8280`.
2. **Create Flow**: Start a new flow.
3. **Add Step**: Search for **Trainium AI**.
4. **Parameters**:
    - **Prompt Name**: Copy from Langfuse (e.g., `JOB_REVIEW_GATEKEEPER`).
    - **Variables**: Map the job description and company name from your webhook trigger.
    - **Model Alias**: Leave blank to use the **Langfuse default**.

## 4. Environment Variable Tip

Ensure the piece knows where to find the Python service. In your `docker-compose.yml` for ActivePieces, you should have:

```yaml
    environment:
      - PYTHON_SERVICE_URL=http://trainium-python-service:8000
```

*(I have verified your `docker-compose.yml` uses the container name `trainium_python_service` for the image, but the service name in the YAML is `python-service`. Use `http://python-service:8000`)*.
