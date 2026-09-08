# GCP Setup — DIRECTOR'S CUT

Project: `director-cut` · Region: `us-central1`

## Enabled APIs
- aiplatform, run, bigquery, cloudtasks, secretmanager, discoveryengine, artifactregistry, cloudbuild

## Service Account
`director-cut-agent@director-cut.iam.gserviceaccount.com` with minimal roles:

| Role | Why |
|---|---|
| roles/aiplatform.user | Agent Engine deploy + Gemini calls |
| roles/secretmanager.secretAccessor | Read Grafana SA token |
| roles/bigquery.dataEditor, roles/bigquery.jobUser | Post-mortems |
| roles/cloudtasks.enqueuer | Remediation commands |
| roles/run.developer | War-room UI deploy |
| roles/discoveryengine.editor | Runbook RAG data store |

## Local auth
```bash
gcloud config set project director-cut
gcloud auth application-default set-quota-project director-cut
```
Secrets live in Secret Manager / `.env` (git-ignored) — never in the repo.
