
# HW3 CDK Infrastructure

Replaces manual AWS Console setup from HW2 with three CDK stacks.

## Stacks

| Stack | Resources |
|-------|-----------|
| `StorageStack` | DynamoDB table (`PK=bucketName`, `SK=timeStamp`) + GSI on `timeStamp` |
| `ComputeStack` | S3 TestBucket + S3 event notifications → `size-tracking` lambda + `plotting` lambda (matplotlib layer + Function URL REST API) |
| `DriverStack` | `driver` lambda — runs the HW2 sequence then calls the plotting REST API |

> The S3 bucket lives in `ComputeStack` (not `StorageStack`) to keep the Lambda event notification in the same stack and avoid a CDK cross-stack cyclic dependency.

## Lambda source

`lambda/` — copies of the three handler files. All config (bucket name, table name, plotting URL) is injected via environment variables; nothing is hardcoded.

## Deploy

```bash
# one-time per account/region
cdk bootstrap --qualifier hw36620

# deploy all three stacks
cdk deploy --all --qualifier hw36620
```

The plotting Function URL is printed as `ComputeStack.PlottingFunctionUrl` and automatically wired into the driver lambda's `PLOTTING_URL` env var.

## Useful commands

```bash
cdk synth       # emit CloudFormation templates (dry-run)
cdk diff        # compare deployed vs local
cdk destroy --all   # tear everything down
```
