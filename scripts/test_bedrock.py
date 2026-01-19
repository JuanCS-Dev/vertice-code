import boto3
import json
import os


def invoke_claude_bedrock():
    print("--- Testing Claude on AWS Bedrock ---")

    # Use default credentials chain (Env vars, ~/.aws/credentials, etc.)
    # We assume the user has configured AWS credentials in their environment.

    region_name = os.getenv("AWS_REGION", "us-east-1")
    model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Latest Sonnet

    print(f"Region: {region_name}")
    print(f"Model: {model_id}")

    try:
        bedrock = boto3.client(service_name="bedrock-runtime", region_name=region_name)

        prompt = "Hello, Claude. Are you running on AWS Bedrock?"

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            }
        )

        print("Invoking...")
        response = bedrock.invoke_model(
            body=body, modelId=model_id, accept="application/json", contentType="application/json"
        )

        response_body = json.loads(response.get("body").read())

        # Extract content
        text = ""
        for content in response_body.get("content", []):
            if content["type"] == "text":
                text += content["text"]

        print("✅ SUCCESS!")
        print(f"Response: {text}")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


if __name__ == "__main__":
    invoke_claude_bedrock()
