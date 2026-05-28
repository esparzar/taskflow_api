#!/bin/bash
# ============================================================
# TaskFlow API — AWS S3 + IAM Setup Guide
# Run these AWS CLI commands to set up S3 and IAM correctly.
# Install AWS CLI first: https://aws.amazon.com/cli/
# ============================================================

BUCKET_NAME="taskflow-api-files"
REGION="us-east-1"
IAM_USER="taskflow-s3-user"
POLICY_NAME="TaskFlowS3Policy"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TaskFlow — AWS S3 + IAM Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Create S3 Bucket
echo "[1/4] Creating S3 bucket: $BUCKET_NAME..."
aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $REGION

# Enable versioning (good practice)
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

# Block all public access (files accessed via presigned URLs)
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "✅ S3 bucket created: $BUCKET_NAME"

# 2. Create IAM policy (least privilege — only S3 access for this bucket)
echo "[2/4] Creating IAM policy..."
POLICY_DOC=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:HeadObject"
            ],
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        },
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::${BUCKET_NAME}"
        }
    ]
}
EOF
)

POLICY_ARN=$(aws iam create-policy \
    --policy-name $POLICY_NAME \
    --policy-document "$POLICY_DOC" \
    --query 'Policy.Arn' \
    --output text)

echo "✅ IAM policy created: $POLICY_ARN"

# 3. Create IAM user
echo "[3/4] Creating IAM user: $IAM_USER..."
aws iam create-user --user-name $IAM_USER
aws iam attach-user-policy \
    --user-name $IAM_USER \
    --policy-arn $POLICY_ARN

echo "✅ IAM user created and policy attached"

# 4. Create access keys
echo "[4/4] Creating access keys..."
KEYS=$(aws iam create-access-key --user-name $IAM_USER)
ACCESS_KEY=$(echo $KEYS | python3 -c "import sys,json; k=json.load(sys.stdin)['AccessKey']; print(k['AccessKeyId'])")
SECRET_KEY=$(echo $KEYS | python3 -c "import sys,json; k=json.load(sys.stdin)['AccessKey']; print(k['SecretAccessKey'])")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ AWS setup complete! Save these values:"
echo ""
echo "  AWS_ACCESS_KEY_ID     = $ACCESS_KEY"
echo "  AWS_SECRET_ACCESS_KEY = $SECRET_KEY"
echo "  AWS_S3_BUCKET         = $BUCKET_NAME"
echo "  AWS_S3_REGION         = $REGION"
echo ""
echo "Add these to:"
echo "  → .env (local dev)"
echo "  → GitHub Secrets (for CI/CD)"
echo "  → EC2 environment variables (for production)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
