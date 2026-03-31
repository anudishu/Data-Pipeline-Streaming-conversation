## System architecture (streaming chat pipeline)

This project models a common real-time analytics pattern: **events come in fast**, we enrich/normalize them, and we land them into **query-friendly tables** with consistent schemas.

### High-level flow

1. **Source data**
   - Demo uses a newline-delimited JSON file (`conversations.json`) stored in **Cloud Storage**.
   - In a real system, the “source” would be application events (mobile app, web chat, order service) publishing directly to Pub/Sub.

2. **Messaging layer (Pub/Sub)**
   - A topic receives individual events (messages).
   - A subscription is used by the streaming pipeline to read messages with at-least-once delivery.

3. **Stream processing (Dataflow / Apache Beam)**
   - Beam pipeline reads raw Pub/Sub messages.
   - Messages are parsed and mapped into two logical streams:
     - **Conversation messages**: chat metadata + timestamps and participants
     - **Orders**: orderId ↔ cityCode enrichment record
   - Output is written to BigQuery in append mode.

4. **Analytics storage (BigQuery)**
   - Two base tables are created by Terraform:
     - `conversations`
     - `orders`
   - The repo includes an example view (`create-view.sql`) that joins both tables and calculates useful conversation-level metrics:
     - first courier/customer message timestamps
     - message counts per participant type
     - first responder delay
     - last known order stage

5. **Visualization (optional)**
   - BigQuery is a natural source for Looker / Looker Studio dashboards.
   - This repo doesn’t ship dashboards, but the schema is designed to make that straightforward.

### Diagram

![System architecture](../GCP-Architect-ETL-GCP-ChatConversation.jpg)

### Data contracts (what the pipeline expects)

The pipeline expects JSON objects where fields may be missing, and will filter out records that can’t be written meaningfully.

- **Conversation-style message** (example fields)
  - `senderAppType` (STRING)
  - `courierId`, `customerId`, `fromId`, `toId`, `orderId` (INTEGER)
  - `orderStage` (STRING)
  - `chatStartedByMessage` (BOOLEAN)
  - `messageSentTime` (RFC3339 timestamp string; written into BigQuery `TIMESTAMP`)

- **Order enrichment record**
  - `orderId` (INTEGER)
  - `cityCode` (STRING)

The current implementation routes each incoming JSON message to either/both outputs using simple field presence checks.

### Failure modes and production hardening

- **Bad JSON / missing fields**
  - Add a dead-letter topic (or a GCS sink) for parse failures and validation errors.
  - Track counts (bad records / total records) as pipeline metrics.

- **Duplicates**
  - Pub/Sub + streaming pipelines are typically at-least-once.
  - If duplicates matter, write with a stable key (e.g., message id) and dedupe downstream, or use BigQuery MERGE patterns into partitioned tables.

- **Backlog / latency**
  - Monitor subscription backlog, Dataflow “system lag”, and BigQuery streaming insert errors.
  - Configure autoscaling and worker sizing based on expected message rate.

- **Schema changes**
  - Version schemas and plan how to roll forward changes (new nullable fields are easiest).

- **Security**
  - Run Dataflow with a dedicated service account.
  - Keep buckets and datasets private; grant least privilege.

### Why two tables?

Separating `orders` from `conversations` mirrors real systems where “reference/enrichment” events arrive independently from message events. It also makes the analytics view (`create-view.sql`) a good example of combining multiple streams into a single reporting layer.

