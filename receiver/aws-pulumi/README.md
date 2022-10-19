# Webhook AWS receiver

This stack provisions the infrastructure through pulumi.
Before running it you should modify the `webhook-receiver:github_secret` value and enter the token that is configured from github.

Once the stack is implemented, the output of `webhook-relay-receiver-rest-endpoint` must be added. For example `https://***.execute-api.us-east-1.amazonaws.com/v1/github-webhook/`.

After this, the consumer component must be configured.