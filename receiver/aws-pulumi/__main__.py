import pulumi
import pulumi_aws as aws
import iam as iam
import json
region = aws.config.region
#Read from stack config
config = pulumi.Config()
#Read key github_secret
github_secret = config.require_secret("github_secret")
custom_stage_name = 'v1'

queue = aws.sqs.Queue("webhook-relay-receiver-sqs",
                      fifo_queue=False)

# Get queue name
queue_name = queue.id.apply(lambda id: id.split('/')[-1])

# Create lambda for receiver
lambda_func = aws.lambda_.Function("webhook-relay-receiver",
                                   role=iam.lambda_role.arn,
                                   runtime="python3.8",
                                   handler="receiver.handler",
                                   code=pulumi.AssetArchive({
                                       '.': pulumi.FileArchive('./lambda/')
                                   }),
                                   environment=aws.lambda_.FunctionEnvironmentArgs(
                                       variables={
                                           "GITHUB_SECRET": github_secret,
                                           "SQS_QUEUE": queue_name,
                                           "SQS_REGION": region
                                       }
                                   )
                                   )

# Create a single Swagger spec route handler for a Lambda function.


def swagger_route_handler(arn):
    return ({
        "x-amazon-apigateway-any-method": {
            "x-amazon-apigateway-integration": {
                "uri": f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{arn}/invocations',
                "passthroughBehavior": "when_no_match",
                "httpMethod": "POST",
                "type": "aws_proxy",
            },
        },
    })


# Create the API Gateway Rest API, using a swagger spec.
rest_api = aws.apigateway.RestApi("webhook-relay-receiver-api",
                                  body=lambda_func.arn.apply(lambda arn: json.dumps({
                                      "swagger": "2.0",
                                      "info": {"title": "api", "version": "1.0"},
                                      "paths": {
                                          "/{proxy+}": swagger_route_handler(arn),
                                      },
                                  })))

# Create a deployment of the Rest API.
deployment = aws.apigateway.Deployment("webhook-relay-receiver-api-deployment",
                                       rest_api=rest_api.id,
                                       # Note: Set to empty to avoid creating an implicit stage, we'll create it
                                       # explicitly below instead.
                                       stage_name="",
                                       )

# Create a stage, which is an addressable instance of the Rest API. Set it to point at the latest deployment.
stage = aws.apigateway.Stage("webhook-relay-receiver-api-stage",
                             rest_api=rest_api.id,
                             deployment=deployment.id,
                             stage_name=custom_stage_name,
                             )

# Give permissions from API Gateway to invoke the Lambda
rest_invoke_permission = aws.lambda_.Permission("webhook-relay-receiver-lambda-permission",
                                                action="lambda:invokeFunction",
                                                function=lambda_func.name,
                                                principal="apigateway.amazonaws.com",
                                                source_arn=deployment.execution_arn.apply(
                                                    lambda arn: arn + "*/*"),
                                                )

# Export the name of the bucket
pulumi.export("webhook-relay-receiver-rest-endpoint",
              deployment.invoke_url.apply(lambda url: url + custom_stage_name + '/{proxy+}'))

# open template readme and read contents into stack output
with open('./README.md') as f:
    pulumi.export('readme', f.read())