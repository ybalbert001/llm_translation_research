#!/usr/bin/env python3
import sys
import json
import boto3
import argparse
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

from functools import wraps
from math import floor
import time
import sys
import threading
from awsglue.utils import getResolvedOptions

# Use monotonic time if available, otherwise fall back to the system clock.
now = time.monotonic if hasattr(time, 'monotonic') else time.time

class RateLimitException(Exception):
    '''
    Rate limit exception class.
    '''
    def __init__(self, message, period_remaining):
        '''
        Custom exception raise when the number of function invocations exceeds
        that imposed by a rate limit. Additionally the exception is aware of
        the remaining time period after which the rate limit is reset.

        :param string message: Custom exception message.
        :param float period_remaining: The time remaining until the rate limit is reset.
        '''
        super(RateLimitException, self).__init__(message)
        self.period_remaining = period_remaining

class RateLimitDecorator(object):
    '''
    Rate limit decorator class.
    '''
    def __init__(self, calls=15, period=900, clock=now, raise_on_limit=True):
        '''
        Instantiate a RateLimitDecorator with some sensible defaults. By
        default the Twitter rate limiting window is respected (15 calls every
        15 minutes).

        :param int calls: Maximum function invocations allowed within a time period. Must be a number greater than 0.
        :param float period: An upper bound time period (in seconds) before the rate limit resets. Must be a number greater than 0.
        :param function clock: An optional function retuning the current time. This is used primarily for testing.
        :param bool raise_on_limit: A boolean allowing the caller to avoiding rasing an exception.
        '''
        self.clamped_calls = max(1, min(sys.maxsize, floor(calls)))
        self.period = period
        self.clock = clock
        self.raise_on_limit = raise_on_limit

        # Initialise the decorator state.
        self.last_reset = clock()
        self.num_calls = 0

        # Add thread safety.
        self.lock = threading.RLock()

    def __call__(self, func):
        '''
        Return a wrapped function that prevents further function invocations if
        previously called within a specified period of time.

        :param function func: The function to decorate.
        :return: Decorated function.
        :rtype: function
        '''
        @wraps(func)
        def wrapper(*args, **kargs):
            '''
            Extend the behaviour of the decoated function, forwarding function
            invocations previously called no sooner than a specified period of
            time. The decorator will raise an exception if the function cannot
            be called so the caller may implement a retry strategy such as an
            exponential backoff.

            :param args: non-keyword variable length argument list to the decorated function.
            :param kargs: keyworded variable length argument list to the decorated function.
            :raises: RateLimitException
            '''
            with self.lock:
                period_remaining = self.__period_remaining()

                # If the time window has elapsed then reset.
                if period_remaining <= 0:
                    self.num_calls = 0
                    self.last_reset = self.clock()

                # Increase the number of attempts to call the function.
                self.num_calls += 1

                # If the number of attempts to call the function exceeds the
                # maximum then raise an exception.
                if self.num_calls > self.clamped_calls:
                    if self.raise_on_limit:
                        raise RateLimitException('too many calls', period_remaining)
                    return

            return func(*args, **kargs)
        return wrapper

    def __period_remaining(self):
        '''
        Return the period remaining for the current rate limit window.

        :return: The remaing period.
        :rtype: float
        '''
        elapsed = self.clock() - self.last_reset
        return self.period - elapsed

limits = RateLimitDecorator

def sleep_and_retry(func):
    '''
    Return a wrapped function that rescues rate limit exceptions, sleeping the
    current thread until rate limit resets.

    :param function func: The function to decorate.
    :return: Decorated function.
    :rtype: function
    '''
    @wraps(func)
    def wrapper(*args, **kargs):
        '''
        Call the rate limited function. If the function raises a rate limit
        exception sleep for the remaing time period and retry the function.

        :param args: non-keyword variable length argument list to the decorated function.
        :param kargs: keyworded variable length argument list to the decorated function.
        '''
        while True:
            try:
                return func(*args, **kargs)
            except RateLimitException as exception:
                time.sleep(exception.period_remaining)
    return wrapper

# record schema
# {"recordId": "meta_All_Beauty_0_0", "modelInput": {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 2048, "stop_sequences": ["</translation>"], "messages": [{"role": "user", "content": [{"type": "text", "text": "你是一位翻译专家，擅长翻译商品title。请精准的把<src>中的商品Title翻译为ru-ru, 输出到<translation> xml tag中。\n<src>Yes to Tomatoes Detoxifying Charcoal Cleanser (Pack of 2) with Charcoal Powder, Tomato Fruit Extract, and Gingko Biloba Leaf Extract, 5 fl. oz.</src>\n"}]}, {"role": "assistant", "content": [{"type": "text", "text": "<translation>"}]}]}}

# inference output schema
# {"modelInput":{"anthropic_version":"bedrock-2023-05-31","max_tokens":2048,"stop_sequences":["</translation>"],"messages":[{"role":"user","content":[{"type":"text","text":"你是一位翻译专家，擅长翻译商品title。请精准的把<src>中的商品Title翻译为ru-ru, 输出到<translation> xml tag中。\n<src>HANSGO Egg Holder for Refrigerator, Deviled Eggs Dispenser Egg Storage Stackable Plastic Egg Containers Hold ups to 10 Eggs</src>\n"}]},{"role":"assistant","content":[{"type":"text","text":"<translation>"}]}]},"modelOutput":{"id":"msg_bdrk_018FaiigbPq6PehfhWM2GMBv","type":"message","role":"assistant","model":"claude-3-haiku-20240307","content":[{"type":"text","text":"HANSGO Держатель для яиц для холодильника, диспенсер для яиц в горшочках, стопки для хранения яиц, пластиковые контейнеры для яиц, вмещающие до 10 яиц"}],"stop_reason":"stop_sequence","stop_sequence":"</translation>","usage":{"input_tokens":111,"output_tokens":73}},"recordId":"meta_Appliances_0_0"}

## InvokeModel Request Body
# {
#     "anthropic_version": "bedrock-2023-05-31", 
#     "anthropic_beta": ["computer-use-2024-10-22"] 
#     "max_tokens": int,
#     "system": string,    
#     "messages": [
#         {
#             "role": string,
#             "content": [
#                 { "type": "image", "source": { "type": "base64", "media_type": "image/jpeg", "data": "content image bytes" } },
#                 { "type": "text", "text": "content text" }
#       ]
#         }
#     ],
#     "temperature": float,
#     "top_p": float,
#     "top_k": int,
#     "tools": [
#         {
#                 "type": "custom",
#                 "name": string,
#                 "description": string,
#                 "input_schema": json
            
#         },
#         { 
#             "type": "computer_20241022",  
#             "name": "computer", 
#             "display_height_px": int,
#             "display_width_px": int,
#             "display_number": 0 int
#         },
#         { 
#             "type": "bash_20241022", 
#             "name": "bash"
#         },
#         { 
#             "type": "text_editor_20241022",
#             "name": "str_replace_editor"
#         }
        
#     ],
#     "tool_choice": {
#         "type" :  string,
#         "name" : string,
#     },
    

 
#     "stop_sequences": [string]
# }              


class BedrockBatchInference:
    def __init__(self, model_id: str, rpm: int):
        """Initialize the batch inference processor"""
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = model_id
        self.rpm = rpm

    @sleep_and_retry
    def invoke_model_with_rate_limit(self, record: Dict) -> Dict:
        """Process a single record through Bedrock's model with rate limiting using the converse API"""
        # Create rate limiter for this instance
        rate_limiter = limits(calls=self.rpm, period=60)
        rate_limited_invoke = rate_limiter(lambda: self._invoke_model(record))
        return rate_limited_invoke()

    def _invoke_model(self, record: Dict) -> Dict:
        """Internal method to invoke the Bedrock model with the given record"""
        try:
            # Extract the model input from the record
            model_input = record.get('modelInput', {})

            payload = json.dumps(model_input)

            if not model_input:
                raise ValueError("No model input found in the record.")

            print(f"model_input: {model_input}")
    
            response = self.bedrock.invoke_model(body=payload, modelId=self.model_id)
            response_body = json.loads(response.get('body').read())
   
            print(f"response_body: {response_body}")
            # Construct the output following the inference output schema
            return {
                'modelInput': model_input,
                'modelOutput': response_body,
                'recordId': record.get('recordId', '')
            }
        except Exception as e:
            print(f"exception: {e}")
            return {
                'modelInput': model_input,
                'modelOutput': {
                    'error': str(e)
                },
                'recordId': record.get('recordId', '')
            }

    def process_batch(self, records: List[Dict], max_workers: int) -> List[Dict]:
        """Process a batch of records using thread pool"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(self.invoke_model_with_rate_limit, records))

def read_jsonl(s3_path: str) -> List[Dict]:
    """Read JSONL data from S3"""
    s3 = boto3.client('s3')
    bucket, key = s3_path.replace('s3://', '').split('/', 1)
    response = s3.get_object(Bucket=bucket, Key=key)
    return [json.loads(line) for line in response['Body'].read().decode('utf-8').splitlines()]

def write_jsonl(data: List[Dict], s3_path: str):
    """Write JSONL data to S3"""
    s3 = boto3.client('s3')
    bucket, key = s3_path.replace('s3://', '').split('/', 1)
    content = '\n'.join(json.dumps(record) for record in data)
    s3.put_object(Bucket=bucket, Key=key, Body=content.encode('utf-8'))

def main():
    """Main execution function"""
    args = getResolvedOptions(sys.argv, ['input_path', 'output_path', 'model_id', 'rpm', 'max_worker'])
    input_path = args['input_path']
    output_path = args['output_path']
    model_id = args['model_id']
    rpm = int(args['rpm'])
    max_worker = int(args.get('max_worker', 10))
    
    # Initialize processor
    processor = BedrockBatchInference(model_id, rpm)
    
    try:
        # Read input data
        print(f"Reading input data from {input_path}")
        all_records = read_jsonl(input_path)
        records = all_records[:1000]
        
        # Process records
        print(f"Processing {len(records)} records...")
        results = processor.process_batch(records, max_worker)
        
        # Write results
        print(f"Writing results to {output_path}")
        write_jsonl(results, output_path)
        
        print("Processing completed successfully")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
