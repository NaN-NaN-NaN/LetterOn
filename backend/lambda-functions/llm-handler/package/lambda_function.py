"""
LetterOn LLM Handler - AWS Lambda Function
Purpose: Process letter content using AWS Bedrock (Claude) for AI analysis
Trigger: Invoked by FastAPI backend via boto3
Input: OCR text only
Output: Structured JSON with categorization and analysis
"""

import json
import boto3
import os
from typing import Dict, Any

# Initialize AWS Bedrock client
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Model configuration
CLAUDE_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for LLM processing.

    Expected event format:
    {
        "text": "The OCR extracted text from the letter..."
    }

    Returns:
    {
        "subject": "string",
        "sender": "string",
        "category": "string",
        "action_status": "string",
        "has_reminder": boolean,
        "action_due_date": "YYYY-MM-DD or null",
        "ai_suggestion": "string",
        "summary": "string",
        "key_points": ["point1", "point2", ...],
        "amount": "number or null",
        "confidence": "high|medium|low"
    }
    """

    try:
        # Parse input
        print(f"Received event: {json.dumps(event)}")
        
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event

        # Extract text from body
        text = body.get('text', '')

        if not text or not text.strip():
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing text field in request body'
                })
            }

        print(f"Processing {len(text)} characters")

        # Analyze the letter
        result = analyze_letter(text)

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        print(f"Lambda error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


def analyze_letter(text: str) -> Dict[str, Any]:
    """
    Analyze letter text and extract structured information.

    Args:
        text: The OCR extracted text from the letter

    Returns:
        Dictionary with structured analysis results
    """

    prompt = f"""You are an AI assistant helping to analyze incoming mail and letters.

Analyze the following letter text and provide a structured response:

Letter Text:
{text}

Please extract and provide:

1. **Subject**: Create a concise subject line for this letter (e.g., "Payment Notice - Invoice #12345")

2. **Sender**: Identify the sender's name or organization

3. **Category**: Classify into one of these categories:
   - financial-billing: Bills, invoices, payment requests
   - official-government: Government, legal, tax documents
   - personal: Personal correspondence, cards, invitations
   - marketing: Advertisements, promotional material
   - financial-banking: Bank statements, investment reports
   - health-medical: Medical records, prescriptions, health insurance
   - miscellaneous: Everything else

4. **Action Status**: Determine urgency:
   - require-action: Requires immediate action (bills, legal deadlines)
   - action-done: Action already completed or acknowledged
   - no-action-needed: Informational only

5. **Has Reminder**: Should this have a reminder? (true/false)

6. **Action Due Date**: If there's a deadline, extract it (format: YYYY-MM-DD, or null if none)

7. **AI Suggestion**: Provide a brief, actionable suggestion for the recipient (1-2 sentences)

8. **Summary**: Brief 2-3 sentence summary of the letter

9. **Key Points**: Extract 3-5 most important points

10. **Amount**: If this is a bill or financial document, extract the total amount owed (number only, or null)

11. **Confidence**: Your confidence in this analysis (high/medium/low)

IMPORTANT: Respond with ONLY valid JSON, no additional text before or after. Use this exact structure:

{{
  "subject": "string",
  "sender": "string",
  "category": "financial-billing",
  "action_status": "require-action",
  "has_reminder": true,
  "action_due_date": "2024-12-31",
  "ai_suggestion": "string",
  "summary": "string",
  "key_points": ["point1", "point2", "point3"],
  "amount": 125.50,
  "confidence": "high"
}}"""

    response = invoke_claude(prompt)

    # Parse JSON response
    try:
        # Extract JSON from response (in case there's extra text)
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")
        
        json_str = response[json_start:json_end]
        result = json.loads(json_str)
        
        # Validate required fields
        required_fields = ['subject', 'sender', 'category', 'action_status', 'has_reminder', 'ai_suggestion']
        for field in required_fields:
            if field not in result:
                result[field] = get_default_value(field)
        
        print(f"Successfully parsed LLM response: {json.dumps(result)}")
        return result
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON parsing error: {str(e)}")
        print(f"Raw response: {response}")
        
        # Fallback with default values
        return {
            'subject': 'Untitled Letter',
            'sender': 'Unknown Sender',
            'category': 'miscellaneous',
            'action_status': 'no-action-needed',
            'has_reminder': False,
            'action_due_date': None,
            'ai_suggestion': 'Please review this letter and determine appropriate action.',
            'summary': text[:200] if len(text) > 200 else text,
            'key_points': [],
            'amount': None,
            'confidence': 'low',
            'raw_response': response[:500]  # Include part of raw response for debugging
        }


def get_default_value(field: str) -> Any:
    """Get default value for a field"""
    defaults = {
        'subject': 'Untitled Letter',
        'sender': 'Unknown Sender',
        'category': 'miscellaneous',
        'action_status': 'no-action-needed',
        'has_reminder': False,
        'action_due_date': None,
        'ai_suggestion': 'Please review this letter.',
        'summary': '',
        'key_points': [],
        'amount': None,
        'confidence': 'low'
    }
    return defaults.get(field, None)


def invoke_claude(prompt: str, max_tokens: int = 2000) -> str:
    """
    Invoke Claude via AWS Bedrock.

    Args:
        prompt: The prompt to send to Claude
        max_tokens: Maximum tokens in response

    Returns:
        Claude's response as a string
    """

    # Prepare request body for Claude
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": 0.3,  # Lower temperature for more consistent structured output
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        print(f"Invoking Bedrock with model: {CLAUDE_MODEL_ID}")
        
        # Invoke Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=CLAUDE_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        # Parse response
        response_body = json.loads(response['body'].read())

        # Extract text from Claude's response
        content_blocks = response_body.get('content', [])
        if content_blocks:
            response_text = content_blocks[0].get('text', '')
            print(f"Received {len(response_text)} characters from Claude")
            return response_text

        raise Exception("No content in Bedrock response")

    except Exception as e:
        print(f"Error invoking Bedrock: {str(e)}")
        raise