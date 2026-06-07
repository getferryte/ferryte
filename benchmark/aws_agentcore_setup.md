# AWS Bedrock AgentCore — beginner setup for The Forgetting Report

This is the only backend that needs the cloud. Everything else runs locally.
It's written for someone who has **never used AWS** — every step is a link plus
exactly what to click. Do them in order. Use the region **`us-west-2` (Oregon)**
the whole way through.

> **What we're proving:** AgentCore Memory ingests raw chat **events**, then
> auto-extracts **long-term memory** (summaries/facts). We plant a secret, confirm
> AgentCore memorized it, delete the original events, and check if it still
> remembers. If it does → that's the leak the report is about.
>
> Cost: a few dollars for a full run. Tear it down (Step 8) when finished.

---

## Step 1 — sign in and set your region

1. Sign in: **https://console.aws.amazon.com/**
2. **Top-right corner**, click the region name and choose **US West (Oregon)
   us-west-2**. (Do this now; AWS is region-specific and we want everything in
   one place.)

## Step 2 — turn on the AI models (Bedrock "Model access")

AgentCore uses Bedrock models to do its memory extraction. You must switch them
on first.

1. Open: **https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/modelaccess**
2. Click **Enable specific models** (or **Manage model access**).
3. Tick these, then **Next → Submit**:
   - **Anthropic → Claude 3.5 Sonnet** (used for summaries)
   - **Amazon → Titan Text Embeddings V2** (used for semantic facts)
4. Wait until each says **Access granted** (usually instant, sometimes a minute).

## Step 3 — create your access key (so the scripts can log in)

1. Open IAM users: **https://us-east-1.console.aws.amazon.com/iam/home#/users**
   (IAM has no region — that's normal.)
2. Click your user name. If you only have a "root" account, that's fine for now —
   click the account menu top-right → **Security credentials** instead.
3. Go to the **Security credentials** tab → scroll to **Access keys** →
   **Create access key**.
4. Choose **Command Line Interface (CLI)** → tick the confirmation → **Next** →
   **Create access key**.
5. **Download the .csv** (or copy both values now — the secret is shown only once).

Now hand those keys to your computer (run in Terminal):

```bash
brew install awscli
aws configure
#   AWS Access Key ID:     <paste from the csv>
#   AWS Secret Access Key: <paste from the csv>
#   Default region name:   us-west-2
#   Default output format: json

aws sts get-caller-identity      # success = it prints your Account number
```

## Step 4 — create the "execution role" AgentCore needs

AgentCore needs permission to call the AI models on your behalf. This is a one-time
**IAM role**.

1. Open IAM roles: **https://us-east-1.console.aws.amazon.com/iam/home#/roles**
2. Click **Create role** (top-right).
3. Under **Trusted entity type**, pick **Custom trust policy**. Delete what's in
   the box and paste this exactly:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": { "Service": "bedrock-agentcore.amazonaws.com" },
       "Action": "sts:AssumeRole"
     }]
   }
   ```
4. Click **Next**. On the permissions page, don't search for anything — just click
   **Next** again (we add permissions in a second).
5. **Role name:** `AgentCoreMemoryExecRole` → **Create role**.
6. Back on the roles list, click **`AgentCoreMemoryExecRole`** → **Add permissions**
   → **Create inline policy** → click the **JSON** tab → paste:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
       "Resource": "*"
     }]
   }
   ```
   → **Next** → **Policy name:** `BedrockInvoke` → **Create policy**.
7. On the role's summary page, **copy the ARN** at the top (looks like
   `arn:aws:iam::123456789012:role/AgentCoreMemoryExecRole`). You'll paste it into
   `.env` in Step 6.

## Step 5 — give *yourself* permission to run the benchmark

Your login also needs permission to create the memory, write/delete events, and
pass the role from Step 4.

1. Open IAM users: **https://us-east-1.console.aws.amazon.com/iam/home#/users** →
   click your user.
   - (If you're using the **root** account, skip this step — root can already do
     everything. Move to Step 6.)
2. **Add permissions** → **Create inline policy** → **JSON** tab → paste:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock-agentcore:CreateEvent",
           "bedrock-agentcore:DeleteEvent",
           "bedrock-agentcore:ListEvents",
           "bedrock-agentcore:RetrieveMemoryRecords",
           "bedrock-agentcore:ListMemoryRecords",
           "bedrock-agentcore:GetMemoryRecord"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "bedrock-agentcore-control:CreateMemory",
           "bedrock-agentcore-control:GetMemory",
           "bedrock-agentcore-control:DeleteMemory"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": "iam:PassRole",
         "Resource": "arn:aws:iam::*:role/AgentCoreMemoryExecRole"
       }
     ]
   }
   ```
   → **Next** → **Policy name:** `FerryteBenchmark` → **Create policy**.

## Step 6 — fill in `benchmark/.env`

Open `~/Documents/recall/benchmark/.env` and add (paste the ARN from Step 4.7):

```bash
AWS_REGION=us-west-2
MEMORY_EXECUTION_ROLE_ARN=arn:aws:iam::<your-account-id>:role/AgentCoreMemoryExecRole
```

## Step 7 — create the memory and run the benchmark

```bash
cd ~/Documents/recall

# create the memory resource
/tmp/bench_venv/bin/python -m benchmark.setup_agentcore --create
```

It prints a `memoryId`. Paste the two lines it tells you into `benchmark/.env`:

```bash
AGENTCORE_MEMORY_ID=<printed id>
AGENTCORE_NAMESPACE=/summaries/{actorId}
```

Wait until it's ready (provisioning takes ~1 min):

```bash
/tmp/bench_venv/bin/python -m benchmark.setup_agentcore --verify   # repeat until status=ACTIVE
```

Then run it:

```bash
/tmp/bench_venv/bin/python -m benchmark.run --backends agentcore --scenarios all
```

The first run is **slow** — extraction is asynchronous, so the harness waits
until AgentCore has actually memorized each canary before deleting it. That's on
purpose (it keeps the test honest).

## Step 8 — tear it down when finished (stops billing)

```bash
/tmp/bench_venv/bin/python -m benchmark.setup_agentcore --delete
```

---

## If something errors

- **`aws: command not found`** → `brew install awscli` didn't finish; re-run it.
- **`get-caller-identity` fails** → re-run `aws configure`; double-check the keys
  and that region is `us-west-2`.
- **`AccessDeniedException` (CreateMemory)** → Step 5 policy missing, or you're in
  the wrong region.
- **`ValidationException` about the role** → the ARN in `.env` is wrong, or the
  trust policy in Step 4.3 wasn't pasted exactly.
- **Benchmark returns BLIND / nothing** → Step 2 model access isn't granted yet.
- **Stuck anywhere** → copy the exact error to me and I'll pinpoint it.

> Don't want to touch the console at all? Tell me and I'll script Steps 4–5 as
> AWS CLI commands you can paste once `aws configure` (Step 3) is done.
