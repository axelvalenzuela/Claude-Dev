# 0006 — S3 → SQS → Lambda → DynamoDB as an asynchronous validation pipeline

**Status:** Accepted

## Context

The user asked for: S3 to store uploaded files, "SQS para todas las
peticiones" (SQS for all requests), a Lambda that validates the uploaded
files, and a DynamoDB table that the Lambda populates with the report
data after validation. Read literally, this describes a decoupled,
asynchronous pipeline rather than the EC2 app validating files
synchronously in the request/response cycle.

## Decision

- The EC2 app uploads a report's files directly to the S3 bucket.
- The S3 bucket is configured with an **Event Notification** that
  publishes to an SQS queue on every `s3:ObjectCreated:*` event —
  this is the concrete meaning of "SQS para todas las peticiones": every
  file upload becomes one queued message, decoupling upload from
  validation so a slow or failing validation never blocks the app's
  response to the user.
- A Lambda function is subscribed to that queue via an
  **event source mapping**, and for each message: fetches the object
  from S3, runs validation (file type/size/structure checks — mirroring
  the kind of checks `lab2/expenses/pdf_analysis.py` and
  `image_analysis.py` already do at upload time, now also enforced
  server-side), and on success writes a validated-report record to
  DynamoDB.
- A **Dead Letter Queue** (a second SQS queue) catches messages the
  Lambda fails to process after retries, so a bad file or a Lambda bug
  doesn't silently drop a report — it becomes an inspectable message
  instead of a lost one.
- The Lambda's execution role only allows `s3:GetObject` on the reports
  bucket, `dynamodb:PutItem`/`UpdateItem` on the reports table, and the
  standard SQS consume permissions on its own queue — nothing broader.

## Alternatives considered

- **Synchronous validation inside the Django request** (no SQS/Lambda at
  all, EC2 validates and writes straight to DynamoDB) — simplest, and
  arguably sufficient at <100 users, but explicitly not what was asked
  for, and loses the retry/DLQ safety net a queue provides for free.
  Rejected in favor of following the explicit requirement.
- **SNS instead of, or in addition to, SQS** — SNS fans out to multiple
  subscribers, useful if several independent consumers needed to react
  to the same upload. Only one consumer (the validation Lambda) exists
  today, so plain SQS is enough; SNS→SQS fan-out is a straightforward
  later addition if a second consumer shows up, without restructuring
  this pipeline.
- **Step Functions to orchestrate multi-stage validation** — overkill
  for a single validate-then-write step; adds a state machine to
  design, deploy, and pay for with no current multi-step workflow to
  justify it.

## Consequences

- Validation is no longer instantaneous from the uploading user's point
  of view — there's a queue-and-Lambda hop between "file uploaded" and
  "report marked validated in DynamoDB." The app's UI needs to reflect a
  pending/processing state rather than assuming validation is done by
  the time the upload HTTP response returns. This is an application-
  level follow-up, not something this infrastructure template can fix
  by itself — noted in `infra/README.md`.
- A failed validation lands in the DLQ, not in front of any human by
  default — a CloudWatch Alarm on the DLQ's `ApproximateNumberOfMessages
  Visible` metric is included so a stuck/failing message actually gets
  noticed rather than sitting silently.
- This pipeline is intentionally decoupled from the app's own request
  path for report *creation* (which still writes to the app's local
  database first, per ADR 0007) — DynamoDB here holds the
  Lambda-validated view of report data, not the system of record for
  the report's initial submission.
