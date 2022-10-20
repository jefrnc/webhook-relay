# Webhook AWS receiver

This stack provisions the infrastructure through pulumi.
Before running it you should modify the `webhook-receiver:github_secret` value and enter the token that is configured from github.

Once the stack is implemented, the output of `webhook-relay-receiver-rest-endpoint` must be added. For example `https://***.execute-api.us-east-1.amazonaws.com/v1/github-webhook/`.

After this, the consumer component must be configured.

Role Policy

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSQS",
            "Effect": "Allow",
            "Action": [
                "sqs:DeleteMessage",
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage"
            ],
            "Resource": "arn:aws:sqs:us-west-2:****:webhook-relay-receiver-sqs-*"
        }
    ]
}
```