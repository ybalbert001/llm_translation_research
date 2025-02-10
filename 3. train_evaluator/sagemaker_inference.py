from typing import Any, Optional, Union, cast
from sagemaker import Predictor, serializers  # type: ignore
from sagemaker.session import Session  # type: ignore
import boto3
import json

def inference(predictor, messages: list[dict[str, Any]], params: dict[str, Any]={}, stop: list=[], stream=False):
    """
    params:
    predictor : Sagemaker Predictor
    messages (List[Dict[str,Any]]): message list。
                messages = [
                {"role": "system", "content":"please answer in Chinese"},
                {"role": "user", "content": "who are you? what are you doing?"},
            ]
    params (Dict[str,Any]): model parameters for LLM。
    stream (bool): False by default。

    response:
    result of inference if stream is False
    Iterator of Chunks if stream is True
    """
    payload = {
        "model": params.get("model_name"),
        "stop": stop,
        "messages": messages,
        "stream": stream,
        "max_tokens": params.get("max_new_tokens", params.get("max_tokens", 2048)),
        "temperature": params.get("temperature", 0.1),
        "top_p": params.get("top_p", 0.9),
    }

    if not stream:
        response = predictor.predict(payload)
        resp_obj = json.loads(response.decode("utf-8"))
        resp_str = resp_obj.get("choices")[0].get("message").get("content")
        return resp_str
    else:
        raise RuntimeError("Not implemented yet..")
    

def get_predictor(endpoint_name: str, aws_region:str, access_key:str=None, secret_key:str=None):
    """
    params:
    endpoint_name (str): sagemaker endpoint name
    session (sagemaker.session.Session): sagemaker session
    model_name (str): model name
    model_kwargs (Dict[str, Any]): model parameters for LLM。

    response:
    sagemaker Predictor
    """
    boto_session = None
    sagemaker_session = None
    if aws_region:
        if access_key and secret_key:
            boto_session = boto3.Session(
                aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=aws_region
            )
        else:
            boto_session = boto3.Session(region_name=aws_region)
    else:
        boto_session = boto3.Session()

    sagemaker_client = boto_session.client("sagemaker")
    sagemaker_session = Session(boto_session=boto_session, sagemaker_client=sagemaker_client)

    predictor = Predictor(
        endpoint_name=endpoint_name,
        session=sagemaker_session,
        serializer=serializers.JSONSerializer(),
    )
    return predictor