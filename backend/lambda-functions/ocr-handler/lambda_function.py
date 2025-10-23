"""
LetterOn OCR Handler - AWS Lambda Function
Purpose: Extract text from images using AWS Textract
Trigger: Invoked by FastAPI backend via boto3
Input: S3 image URL(s)
Output: Extracted OCR text

This Lambda function:
1. Receives image S3 keys from the backend
2. Uses AWS Textract to extract text from images
3. Returns structured OCR results
"""

import json
import boto3
import os
from typing import Dict, List, Any

# Initialize AWS clients
textract = boto3.client('textract')
s3 = boto3.client('s3')

# Configuration from environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'letteron-images')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for OCR processing.

    Expected event format:
    {
        "s3_keys": ["letters/image1.jpg", "letters/image2.jpg"],
        "bucket": "letteron-images"  # Optional, defaults to env var
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "ocr_results": [
                {
                    "s3_key": "letters/image1.jpg",
                    "text": "Extracted text...",
                    "confidence": 95.5,
                    "blocks": [...]  # Raw Textract blocks
                }
            ]
        }
    }
    """

    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event

        s3_keys = body.get('s3_keys', [])
        bucket = body.get('bucket', S3_BUCKET_NAME)

        if not s3_keys:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required field: s3_keys'
                })
            }

        print(f"Processing {len(s3_keys)} images from bucket: {bucket}")

        # Process each image
        ocr_results = []
        for s3_key in s3_keys:
            try:
                result = process_image(bucket, s3_key)
                ocr_results.append(result)
            except Exception as e:
                print(f"Error processing {s3_key}: {str(e)}")
                ocr_results.append({
                    's3_key': s3_key,
                    'error': str(e),
                    'text': '',
                    'confidence': 0.0
                })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'ocr_results': ocr_results,
                'total_processed': len(ocr_results)
            })
        }

    except Exception as e:
        print(f"Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


def process_image(bucket: str, s3_key: str) -> Dict[str, Any]:
    """
    Process a single image using AWS Textract.

    Args:
        bucket: S3 bucket name
        s3_key: S3 object key

    Returns:
        Dictionary with OCR results
    """
    print(f"Processing image: s3://{bucket}/{s3_key}")

    # Call Textract
    response = textract.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': s3_key
            }
        }
    )

    # Extract text and confidence
    blocks = response.get('Blocks', [])

    # Combine all LINE blocks to get full text
    extracted_text = []
    total_confidence = 0
    line_count = 0

    for block in blocks:
        if block['BlockType'] == 'LINE':
            extracted_text.append(block.get('Text', ''))
            total_confidence += block.get('Confidence', 0)
            line_count += 1

    full_text = '\n'.join(extracted_text)
    avg_confidence = total_confidence / line_count if line_count > 0 else 0

    print(f"Extracted {len(full_text)} characters with {avg_confidence:.2f}% confidence")

    return {
        's3_key': s3_key,
        'text': full_text,
        'confidence': round(avg_confidence, 2),
        'line_count': line_count,
        'blocks': blocks  # Include raw blocks for advanced processing
    }


def get_document_analysis(bucket: str, s3_key: str) -> Dict[str, Any]:
    """
    Advanced document analysis using Textract (for structured documents).

    This is more expensive but provides forms, tables, and key-value pairs.
    Use this for official documents, forms, invoices, etc.

    Args:
        bucket: S3 bucket name
        s3_key: S3 object key

    Returns:
        Dictionary with detailed document analysis
    """
    response = textract.analyze_document(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': s3_key
            }
        },
        FeatureTypes=['TABLES', 'FORMS']
    )

    # Extract key-value pairs
    key_values = extract_key_values(response)

    # Extract tables
    tables = extract_tables(response)

    return {
        's3_key': s3_key,
        'key_values': key_values,
        'tables': tables,
        'blocks': response.get('Blocks', [])
    }


def extract_key_values(response: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract key-value pairs from Textract response."""
    key_values = []
    blocks = response.get('Blocks', [])

    # Create a map of block IDs to blocks
    block_map = {block['Id']: block for block in blocks}

    for block in blocks:
        if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
            key_text = get_text_from_relationship(block, block_map, 'CHILD')
            value_text = ''

            # Find the VALUE block
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'VALUE':
                        for value_id in relationship['Ids']:
                            value_block = block_map.get(value_id)
                            if value_block:
                                value_text = get_text_from_relationship(value_block, block_map, 'CHILD')

            if key_text:
                key_values.append({
                    'key': key_text,
                    'value': value_text
                })

    return key_values


def extract_tables(response: Dict[str, Any]) -> List[List[List[str]]]:
    """Extract tables from Textract response."""
    tables = []
    blocks = response.get('Blocks', [])

    block_map = {block['Id']: block for block in blocks}

    for block in blocks:
        if block['BlockType'] == 'TABLE':
            table = []
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for cell_id in relationship['Ids']:
                            cell_block = block_map.get(cell_id)
                            if cell_block and cell_block['BlockType'] == 'CELL':
                                row_index = cell_block.get('RowIndex', 0) - 1
                                col_index = cell_block.get('ColumnIndex', 0) - 1

                                # Ensure table has enough rows
                                while len(table) <= row_index:
                                    table.append([])

                                # Ensure row has enough columns
                                while len(table[row_index]) <= col_index:
                                    table[row_index].append('')

                                # Get cell text
                                cell_text = get_text_from_relationship(cell_block, block_map, 'CHILD')
                                table[row_index][col_index] = cell_text

            if table:
                tables.append(table)

    return tables


def get_text_from_relationship(block: Dict, block_map: Dict, relationship_type: str) -> str:
    """Helper function to extract text from block relationships."""
    text = ''
    if 'Relationships' in block:
        for relationship in block['Relationships']:
            if relationship['Type'] == relationship_type:
                for child_id in relationship['Ids']:
                    word_block = block_map.get(child_id)
                    if word_block and word_block['BlockType'] == 'WORD':
                        text += word_block.get('Text', '') + ' '
    return text.strip()
