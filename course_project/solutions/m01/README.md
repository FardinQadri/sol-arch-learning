# shortly-infra

The infrastructure-as-code for Shortly, the URL shortener you build up across the course. Each milestone adds one layer of CloudFormation templates, with parameter files for the lab and prod environments.

## Layers

| Layer | What it holds | Milestone |
|-------|---------------|-----------|
| `iam` | Roles for the app, the click consumer, the deployer and the auditor | M01 |

## Check it

Run the milestone tests with the course venv:

```
python run_milestone.py 1
```

## Deploy (optional)

Deploying to a real account is optional; see the course's `DEPLOY.md`.
