"""One-time setup for the AWS Bedrock AgentCore Memory backend.

Creates a Memory resource with a summarization + semantic strategy (the derived
long-term memory that the benchmark probes), then prints the memoryId to drop
into benchmark/.env as AGENTCORE_MEMORY_ID.

    python -m benchmark.setup_agentcore --create     # create the memory
    python -m benchmark.setup_agentcore --verify      # check identity + memory
    python -m benchmark.setup_agentcore --delete      # tear it down

Needs (in benchmark/.env or your AWS env):
    AWS_REGION=us-west-2
    MEMORY_EXECUTION_ROLE_ARN=arn:aws:iam::<acct>:role/<AgentCoreMemoryRole>
And AWS credentials configured via `aws configure` (see aws_agentcore_setup.md).
"""

from __future__ import annotations

import argparse
import os

from .run import load_env

MEMORY_NAME = "ferryte_forgetting_bench"


def _client(service: str):
    import boto3  # noqa: PLC0415

    return boto3.client(service, region_name=os.environ.get("AWS_REGION", "us-west-2"))


def verify() -> None:
    sts = _client("sts")
    ident = sts.get_caller_identity()
    print(f"AWS account: {ident['Account']}  (arn: {ident['Arn']})")
    mem_id = os.environ.get("AGENTCORE_MEMORY_ID")
    if not mem_id:
        print("AGENTCORE_MEMORY_ID not set yet — run --create first.")
        return
    ctl = _client("bedrock-agentcore-control")
    m = ctl.get_memory(memoryId=mem_id)["memory"]
    print(f"Memory {mem_id}: status={m.get('status')} strategies={len(m.get('strategies', []))}")


def create() -> None:
    role = os.environ.get("MEMORY_EXECUTION_ROLE_ARN")
    if not role:
        raise SystemExit("Set MEMORY_EXECUTION_ROLE_ARN in benchmark/.env first.")
    ctl = _client("bedrock-agentcore-control")
    resp = ctl.create_memory(
        name=MEMORY_NAME,
        description="Ferryte 'Forgetting Report' benchmark — delete-after-revoke test.",
        eventExpiryDuration=90,
        memoryExecutionRoleArn=role,
        memoryStrategies=[
            {
                "semanticMemoryStrategy": {
                    "name": "bench_semantic",
                    "namespaces": ["/facts/{actorId}"],
                }
            },
        ],
    )
    mem = resp["memory"]
    mid = mem.get("id") or mem.get("memoryId")
    print(f"Created memory: {mid}  (status={mem.get('status')})")
    print("\nAdd this to benchmark/.env:")
    print(f"  AGENTCORE_MEMORY_ID={mid}")
    print("  AGENTCORE_NAMESPACE=/facts/{actorId}")
    print("\nWait until status=ACTIVE (run --verify) before benchmarking.")


def delete() -> None:
    mem_id = os.environ.get("AGENTCORE_MEMORY_ID")
    if not mem_id:
        raise SystemExit("AGENTCORE_MEMORY_ID not set.")
    _client("bedrock-agentcore-control").delete_memory(memoryId=mem_id)
    print(f"Delete requested for {mem_id}.")


if __name__ == "__main__":
    load_env()
    ap = argparse.ArgumentParser(description="AgentCore Memory setup for the benchmark")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--create", action="store_true")
    g.add_argument("--verify", action="store_true")
    g.add_argument("--delete", action="store_true")
    args = ap.parse_args()
    if args.create:
        create()
    elif args.verify:
        verify()
    else:
        delete()
