
# HW2 CDK Infrastructure

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
cdk bootstrap

# deploy all three stacks
cdk deploy --all
```

The plotting Function URL is printed as `ComputeStack.PlottingFunctionUrl` and automatically wired into the driver lambda's `PLOTTING_URL` env var.

## Useful commands

```bash
cdk synth       # emit CloudFormation templates (dry-run)
cdk diff        # compare deployed vs local
cdk destroy --all   # tear everything down
```

---
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `requirements.txt` file and rerun the `python -m pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
