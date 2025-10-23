"""
LetterOn Server - AWS Lambda Client
Purpose: Wrapper for invoking AWS Lambda functions (OCR and LLM handlers)
Testing: Mock boto3 lambda client in tests
AWS Deployment: Ensure Lambda execution permissions in IAM role

This module provides a clean interface for invoking the existing Lambda functions:
- LetterOnOCRHandler: Processes images with Textract OCR
- LetterOnLLMHandler: Analyzes text with AWS Bedrock LLM

DO NOT re-implement OCR/LLM logic here - always call the Lambda functions.
"""

import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

from app.settings import settings

logger = logging.getLogger(__name__)


class LambdaClient:
    """
    Client for invoking AWS Lambda functions.

    Handles synchronous and asynchronous invocations with proper error handling.
    """

    def __init__(self):
        """Initialize boto3 Lambda client with configured credentials."""
        aws_config = settings.get_aws_credentials()
        self.client = boto3.client('lambda', **aws_config)
        logger.info(f"Lambda client initialized for region: {settings.aws_region}")

    def invoke_lambda(
        self,
        function_name: str,
        payload: Dict[str, Any],
        sync: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke a Lambda function with the given payload.

        Args:
            function_name: Name of the Lambda function to invoke
            payload: Dictionary payload to send to the Lambda
            sync: If True, wait for response (RequestResponse). If False, async (Event)

        Returns:
            Dict containing the Lambda response, or None if async invocation

        Raises:
            Exception: If Lambda invocation fails
        """
        invocation_type = 'RequestResponse' if sync else 'Event'

        try:
            logger.info(f"Invoking Lambda: {function_name} (type: {invocation_type})")
            logger.debug(f"Payload: {json.dumps(payload)}")

            response = self.client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )

            # For async invocations, just return success
            if not sync:
                logger.info(f"Async Lambda invocation successful: {function_name}")
                return None

            # For sync invocations, parse and return response
            status_code = response.get('StatusCode', 0)
            logger.info(f"Lambda response status: {status_code}")

            if status_code != 200:
                error_msg = f"Lambda invocation failed with status {status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Read and parse response payload
            response_payload = response['Payload'].read()
            result = json.loads(response_payload)

            # Check for Lambda function errors
            if 'FunctionError' in response:
                error_msg = f"Lambda function error: {result}"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.info(f"Lambda invocation successful: {function_name}")
            logger.debug(f"Response: {json.dumps(result)}")

            return result

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"AWS ClientError invoking Lambda {function_name}: {error_code} - {error_msg}")
            raise Exception(f"Failed to invoke Lambda {function_name}: {error_msg}")

        except Exception as e:
            logger.error(f"Error invoking Lambda {function_name}: {str(e)}", exc_info=True)
            raise

    def invoke_ocr_lambda(self, s3_keys: list[str]) -> Dict[str, Any]:
        """
        Invoke the OCR Lambda function to extract text from images.

        Args:
            s3_keys: List of S3 object keys for the images to process

        Returns:
            Dict containing OCR results with structure:
            {
                "text": "extracted text content",
                "pages": [
                    {
                        "page_number": 1,
                        "text": "page 1 text",
                        "confidence": 0.95
                    }
                ],
                "metadata": {...}
            }

        Example:
            result = lambda_client.invoke_ocr_lambda([
                "letters/123/image1.jpg",
                "letters/123/image2.jpg"
            ])
        """
        payload = {
            "bucket": settings.s3_bucket_name,
            "s3_keys": s3_keys
        }
        print("=====@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",payload)
        logger.info(f"Invoking OCR Lambda for {len(s3_keys)} images")
        result = self.invoke_lambda(
            function_name=settings.lambda_ocr_function_name,
            payload=payload,
            sync=True
        )

        return result

    def invoke_llm_lambda(
        self,
        text: str,
        prompt_template: str,
        conversation_history: Optional[list] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Invoke the LLM Lambda function for text analysis or chat.

        Args:
            input_text: The text to analyze (OCR text, user question, etc.)
            prompt_template: The prompt template to use
            conversation_history: Optional list of previous messages for chat
            temperature: LLM temperature (0.0-1.0, default 0.7)
            max_tokens: Maximum tokens in response (default 2000)

        Returns:
            Dict containing LLM response with structure:
            {
                "response": "LLM generated text",
                "metadata": {
                    "model": "anthropic.claude-v2",
                    "tokens_used": 1234
                }
            }

        Example for analysis:
            result = lambda_client.invoke_llm_lambda(
                input_text=ocr_text,
                prompt_template=analysis_prompt
            )

        Example for chat:
            result = lambda_client.invoke_llm_lambda(
                input_text="What is the due date?",
                prompt_template=chat_prompt,
                conversation_history=[
                    {"role": "user", "content": "Tell me about this letter"},
                    {"role": "assistant", "content": "This is a bill..."}
                ]
            )
        """
        payload = {
            "text": text,
            "prompt_template": prompt_template,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if conversation_history:
            payload["conversation_history"] = conversation_history

        logger.info(f"Invoking LLM Lambda (temperature: {temperature})")
        print("**********************************",payload)
        result = self.invoke_lambda(
            function_name=settings.lambda_llm_function_name,
            payload=payload,
            sync=True
        )

        return result


# Global Lambda client instance
lambda_client = LambdaClient()
