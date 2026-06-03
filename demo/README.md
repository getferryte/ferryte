# Ferryte demo

## The 30-second X demo

```bash
python demo/multi_tenant_leak.py
```

What happens:

1. Two tenants share an agent. Acme writes a secret. The platform calls the backend's official delete API.
2. The agent answers a follow-up — and still leaks the secret. The delete only removed the primary record; a derived per-tenant summary absorbed the secret and survives. This is the exact behaviour AWS Bedrock AgentCore and Zep document.
3. Ferryte is turned on. The same scenario runs as a test. The leak is caught, classified, and an HTML/JSON report is produced.

The demo uses the bundled in-memory vector store so it runs anywhere with zero external dependencies or API keys.

## How to swap in a real backend

The included `InMemoryVectorStore` is built to **mirror** the public failure modes of real agent-memory backends:

| Backend         | Documented failure mode this demo reproduces |
| --------------- | -------------------------------------------- |
| AWS Bedrock AgentCore | `DeleteEvent` does not remove derived long-term memory records ([source](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/short-term-delete-event.html)) |
| Zep / Graphiti  | Deleting an episode does not regenerate the shared node summaries that absorbed it |
| Mem0 over a vector index | Row delete leaves embeddings in the retrieval cache until reindex |

To run the same scenarios against real Mem0, install Ferryte with the Mem0 extra and have the Mem0 server reachable:

```bash
pip install "ferryte[mem0]"
python -c "import ferryte, mem0; ferryte.instrument(); m = mem0.Memory(); ..."
ferryte test --scenario source-revocation
```

The Zep and AgentCore adapters are part of the next milestone; the adapter interface in `src/ferryte/adapters/base.py` is the only thing you need to implement.
