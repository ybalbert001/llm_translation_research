import boto3

def delete_manifest_files(bucket_name, prefix):
    """
    删除指定S3桶和前缀下所有子目录中的manifest.json.out文件
    
    :param bucket_name: S3桶名称
    :param prefix: S3路径前缀
    """
    s3 = boto3.client('s3')
    
    # 确保前缀以'/'结尾
    if not prefix.endswith('/'):
        prefix += '/'
    
    # 列出所有对象
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('manifest.json.out'):
                    try:
                        s3.delete_object(Bucket=bucket_name, Key=key)
                        print(f"Deleted: {key}")
                    except ClientError as e:
                        print(f"Error deleting {key}: {e}")

# 使用示例
bucket_name = 'translation-quality-check-model-sft-20241203'
prefix = 'amazon-review-product-meta-data/batch-inference-output/'

delete_manifest_files(bucket_name, prefix)