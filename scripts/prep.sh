#!/usr/bin/env bash

export AWS_REGION=$(aws configure get region)
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account 
--output text)

RANDOM_SUFFIX=$(aws secretsmanager get-random-password --exclude-punctuation --exclude-uppercase --password-length 6 --require-each-included-type --output text --query RandomPassword)


export LAMBDA_FUNCTION_NAME="contact-form-processor-${RANDOM_SUFFIX}"
export API_GATEWAY_NAME="contact-form-api-${RANDOM_SUFFIX}"
export IAM_ROLE_NAME="contact-form-lambda-role-${RANDOM_SUFFIX}"

aws ses describe-configuration-set \
  --configuration-set-name default || true

echo "AWS region: $AWS_REGION"
echo "Account ID: $AWS_ACCOUNT_ID"
echo "Suffix: $RANDOM_SUFFIX"
