import json
from datetime import datetime

import boto3
import sure  # noqa
from botocore.exceptions import ClientError
from nose.tools import assert_raises

from moto import mock_codepipeline, mock_iam


@mock_codepipeline
def test_create_pipeline():
    client = boto3.client("codepipeline", region_name="us-east-1")

    response = create_basic_codepipeline(client, "test-pipeline")

    response["pipeline"].should.equal(
        {
            "name": "test-pipeline",
            "roleArn": "arn:aws:iam::123456789012:role/test-role",
            "artifactStore": {
                "type": "S3",
                "location": "codepipeline-us-east-1-123456789012",
            },
            "stages": [
                {
                    "name": "Stage-1",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Source",
                                "owner": "AWS",
                                "provider": "S3",
                                "version": "1",
                            },
                            "runOrder": 1,
                            "configuration": {
                                "S3Bucket": "test-bucket",
                                "S3ObjectKey": "test-object",
                            },
                            "outputArtifacts": [{"name": "artifact"}],
                            "inputArtifacts": [],
                        }
                    ],
                },
                {
                    "name": "Stage-2",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Approval",
                                "owner": "AWS",
                                "provider": "Manual",
                                "version": "1",
                            },
                            "runOrder": 1,
                            "configuration": {},
                            "outputArtifacts": [],
                            "inputArtifacts": [],
                        }
                    ],
                },
            ],
            "version": 1,
        }
    )
    response["tags"].should.equal([{"key": "key", "value": "value"}])


@mock_codepipeline
@mock_iam
def test_create_pipeline_errors():
    client = boto3.client("codepipeline", region_name="us-east-1")
    client_iam = boto3.client("iam", region_name="us-east-1")
    create_basic_codepipeline(client, "test-pipeline")

    with assert_raises(ClientError) as e:
        create_basic_codepipeline(client, "test-pipeline")
    ex = e.exception
    ex.operation_name.should.equal("CreatePipeline")
    ex.response["ResponseMetadata"]["HTTPStatusCode"].should.equal(400)
    ex.response["Error"]["Code"].should.contain("InvalidStructureException")
    ex.response["Error"]["Message"].should.equal(
        "A pipeline with the name 'test-pipeline' already exists in account '123456789012'"
    )

    with assert_raises(ClientError) as e:
        client.create_pipeline(
            pipeline={
                "name": "invalid-pipeline",
                "roleArn": "arn:aws:iam::123456789012:role/not-existing",
                "artifactStore": {
                    "type": "S3",
                    "location": "codepipeline-us-east-1-123456789012",
                },
                "stages": [
                    {
                        "name": "Stage-1",
                        "actions": [
                            {
                                "name": "Action-1",
                                "actionTypeId": {
                                    "category": "Source",
                                    "owner": "AWS",
                                    "provider": "S3",
                                    "version": "1",
                                },
                                "runOrder": 1,
                            },
                        ],
                    },
                ],
            }
        )
    ex = e.exception
    ex.operation_name.should.equal("CreatePipeline")
    ex.response["ResponseMetadata"]["HTTPStatusCode"].should.equal(400)
    ex.response["Error"]["Code"].should.contain("InvalidStructureException")
    ex.response["Error"]["Message"].should.equal(
        "CodePipeline is not authorized to perform AssumeRole on role arn:aws:iam::123456789012:role/not-existing"
    )

    wrong_role_arn = client_iam.create_role(
        RoleName="wrong-role",
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "s3.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
    )["Role"]["Arn"]

    with assert_raises(ClientError) as e:
        client.create_pipeline(
            pipeline={
                "name": "invalid-pipeline",
                "roleArn": wrong_role_arn,
                "artifactStore": {
                    "type": "S3",
                    "location": "codepipeline-us-east-1-123456789012",
                },
                "stages": [
                    {
                        "name": "Stage-1",
                        "actions": [
                            {
                                "name": "Action-1",
                                "actionTypeId": {
                                    "category": "Source",
                                    "owner": "AWS",
                                    "provider": "S3",
                                    "version": "1",
                                },
                                "runOrder": 1,
                            },
                        ],
                    },
                ],
            }
        )
    ex = e.exception
    ex.operation_name.should.equal("CreatePipeline")
    ex.response["ResponseMetadata"]["HTTPStatusCode"].should.equal(400)
    ex.response["Error"]["Code"].should.contain("InvalidStructureException")
    ex.response["Error"]["Message"].should.equal(
        "CodePipeline is not authorized to perform AssumeRole on role arn:aws:iam::123456789012:role/wrong-role"
    )

    with assert_raises(ClientError) as e:
        client.create_pipeline(
            pipeline={
                "name": "invalid-pipeline",
                "roleArn": get_role_arn(),
                "artifactStore": {
                    "type": "S3",
                    "location": "codepipeline-us-east-1-123456789012",
                },
                "stages": [
                    {
                        "name": "Stage-1",
                        "actions": [
                            {
                                "name": "Action-1",
                                "actionTypeId": {
                                    "category": "Source",
                                    "owner": "AWS",
                                    "provider": "S3",
                                    "version": "1",
                                },
                                "runOrder": 1,
                            },
                        ],
                    },
                ],
            }
        )
    ex = e.exception
    ex.operation_name.should.equal("CreatePipeline")
    ex.response["ResponseMetadata"]["HTTPStatusCode"].should.equal(400)
    ex.response["Error"]["Code"].should.contain("InvalidStructureException")
    ex.response["Error"]["Message"].should.equal(
        "Pipeline has only 1 stage(s). There should be a minimum of 2 stages in a pipeline"
    )


@mock_codepipeline
def test_get_pipeline():
    client = boto3.client("codepipeline", region_name="us-east-1")
    create_basic_codepipeline(client, "test-pipeline")

    response = client.get_pipeline(name="test-pipeline")

    response["pipeline"].should.equal(
        {
            "name": "test-pipeline",
            "roleArn": "arn:aws:iam::123456789012:role/test-role",
            "artifactStore": {
                "type": "S3",
                "location": "codepipeline-us-east-1-123456789012",
            },
            "stages": [
                {
                    "name": "Stage-1",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Source",
                                "owner": "AWS",
                                "provider": "S3",
                                "version": "1",
                            },
                            "runOrder": 1,
                            "configuration": {
                                "S3Bucket": "test-bucket",
                                "S3ObjectKey": "test-object",
                            },
                            "outputArtifacts": [{"name": "artifact"}],
                            "inputArtifacts": [],
                        }
                    ],
                },
                {
                    "name": "Stage-2",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Approval",
                                "owner": "AWS",
                                "provider": "Manual",
                                "version": "1",
                            },
                            "runOrder": 1,
                            "configuration": {},
                            "outputArtifacts": [],
                            "inputArtifacts": [],
                        }
                    ],
                },
            ],
            "version": 1,
        }
    )
    response["metadata"]["pipelineArn"].should.equal(
        "arn:aws:codepipeline:us-east-1:123456789012:test-pipeline"
    )
    response["metadata"]["created"].should.be.a(datetime)
    response["metadata"]["updated"].should.be.a(datetime)


@mock_codepipeline
def test_get_pipeline_errors():
    client = boto3.client("codepipeline", region_name="us-east-1")

    with assert_raises(ClientError) as e:
        client.get_pipeline(name="not-existing")
    ex = e.exception
    ex.operation_name.should.equal("GetPipeline")
    ex.response["ResponseMetadata"]["HTTPStatusCode"].should.equal(400)
    ex.response["Error"]["Code"].should.contain("PipelineNotFoundException")
    ex.response["Error"]["Message"].should.equal(
        "Account '123456789012' does not have a pipeline with name 'not-existing'"
    )


@mock_codepipeline
def test_update_pipeline():
    client = boto3.client("codepipeline", region_name="us-east-1")
    create_basic_codepipeline(client, "test-pipeline")

    response = client.get_pipeline(name="test-pipeline")
    created_time = response["metadata"]["created"]
    updated_time = response["metadata"]["updated"]

    response = client.update_pipeline(
        pipeline={
            "name": "test-pipeline",
            "roleArn": get_role_arn(),
            "artifactStore": {
                "type": "S3",
                "location": "codepipeline-us-east-1-123456789012",
            },
            "stages": [
                {
                    "name": "Stage-1",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Source",
                                "owner": "AWS",
                                "provider": "S3",
                                "version": "1",
                            },
                            "configuration": {
                                "S3Bucket": "different-bucket",
                                "S3ObjectKey": "test-object",
                            },
                            "outputArtifacts": [{"name": "artifact"},],
                        },
                    ],
                },
                {
                    "name": "Stage-2",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Approval",
                                "owner": "AWS",
                                "provider": "Manual",
                                "version": "1",
                            },
                        },
                    ],
                },
            ],
        }
    )

    response["pipeline"].should.equal(
        {
            "name": "test-pipeline",
            "roleArn": "arn:aws:iam::123456789012:role/test-role",
            "artifactStore": {
                "type": "S3",
                "location": "codepipeline-us-east-1-123456789012",
            },
            "stages": [
                {
                    "name": "Stage-1",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Source",
                                "owner": "AWS",
                                "provider": "S3",
                                "version": "1",
                            },
                            "runOrder": 1,
                            "configuration": {
                                "S3Bucket": "different-bucket",
                                "S3ObjectKey": "test-object",
                            },
                            "outputArtifacts": [{"name": "artifact"}],
                            "inputArtifacts": [],
                        }
                    ],
                },
                {
                    "name": "Stage-2",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Approval",
                                "owner": "AWS",
                                "provider": "Manual",
                                "version": "1",
                            },
                            "runOrder": 1,
                            "configuration": {},
                            "outputArtifacts": [],
                            "inputArtifacts": [],
                        }
                    ],
                },
            ],
            "version": 2,
        }
    )

    metadata = client.get_pipeline(name="test-pipeline")["metadata"]
    metadata["created"].should.equal(created_time)
    metadata["updated"].should.be.greater_than(updated_time)


@mock_codepipeline
def test_update_pipeline_errors():
    client = boto3.client("codepipeline", region_name="us-east-1")

    with assert_raises(ClientError) as e:
        client.update_pipeline(
            pipeline={
                "name": "not-existing",
                "roleArn": get_role_arn(),
                "artifactStore": {
                    "type": "S3",
                    "location": "codepipeline-us-east-1-123456789012",
                },
                "stages": [
                    {
                        "name": "Stage-1",
                        "actions": [
                            {
                                "name": "Action-1",
                                "actionTypeId": {
                                    "category": "Source",
                                    "owner": "AWS",
                                    "provider": "S3",
                                    "version": "1",
                                },
                                "configuration": {
                                    "S3Bucket": "test-bucket",
                                    "S3ObjectKey": "test-object",
                                },
                                "outputArtifacts": [{"name": "artifact"},],
                            },
                        ],
                    },
                    {
                        "name": "Stage-2",
                        "actions": [
                            {
                                "name": "Action-1",
                                "actionTypeId": {
                                    "category": "Approval",
                                    "owner": "AWS",
                                    "provider": "Manual",
                                    "version": "1",
                                },
                            },
                        ],
                    },
                ],
            }
        )
    ex = e.exception
    ex.operation_name.should.equal("UpdatePipeline")
    ex.response["ResponseMetadata"]["HTTPStatusCode"].should.equal(400)
    ex.response["Error"]["Code"].should.contain("ResourceNotFoundException")
    ex.response["Error"]["Message"].should.equal(
        "The account with id '123456789012' does not include a pipeline with the name 'not-existing'"
    )


@mock_codepipeline
def test_list_pipelines():
    client = boto3.client("codepipeline", region_name="us-east-1")
    name_1 = "test-pipeline-1"
    create_basic_codepipeline(client, name_1)
    name_2 = "test-pipeline-2"
    create_basic_codepipeline(client, name_2)

    response = client.list_pipelines()

    response["pipelines"].should.have.length_of(2)
    response["pipelines"][0]["name"].should.equal(name_1)
    response["pipelines"][0]["version"].should.equal(1)
    response["pipelines"][0]["created"].should.be.a(datetime)
    response["pipelines"][0]["updated"].should.be.a(datetime)
    response["pipelines"][1]["name"].should.equal(name_2)
    response["pipelines"][1]["version"].should.equal(1)
    response["pipelines"][1]["created"].should.be.a(datetime)
    response["pipelines"][1]["updated"].should.be.a(datetime)


@mock_codepipeline
def test_delete_pipeline():
    client = boto3.client("codepipeline", region_name="us-east-1")
    name = "test-pipeline"
    create_basic_codepipeline(client, name)
    client.list_pipelines()["pipelines"].should.have.length_of(1)

    client.delete_pipeline(name=name)

    client.list_pipelines()["pipelines"].should.have.length_of(0)

    # deleting a not existing pipeline, should raise no exception
    client.delete_pipeline(name=name)


@mock_codepipeline
def test_list_tags_for_resource():
    client = boto3.client("codepipeline", region_name="us-east-1")
    name = "test-pipeline"
    create_basic_codepipeline(client, name)

    response = client.list_tags_for_resource(
        resourceArn="arn:aws:codepipeline:us-east-1:123456789012:{}".format(name)
    )
    response["tags"].should.equal([{"key": "key", "value": "value"}])


@mock_codepipeline
def test_list_tags_for_resource_errors():
    client = boto3.client("codepipeline", region_name="us-east-1")

    with assert_raises(ClientError) as e:
        client.list_tags_for_resource(
            resourceArn="arn:aws:codepipeline:us-east-1:123456789012:not-existing"
        )
    ex = e.exception
    ex.operation_name.should.equal("ListTagsForResource")
    ex.response["ResponseMetadata"]["HTTPStatusCode"].should.equal(400)
    ex.response["Error"]["Code"].should.contain("ResourceNotFoundException")
    ex.response["Error"]["Message"].should.equal(
        "The account with id '123456789012' does not include a pipeline with the name 'not-existing'"
    )


@mock_iam
def get_role_arn():
    client = boto3.client("iam", region_name="us-east-1")
    try:
        return client.get_role(RoleName="test-role")["Role"]["Arn"]
    except ClientError:
        return client.create_role(
            RoleName="test-role",
            AssumeRolePolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "codepipeline.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }
                    ],
                }
            ),
        )["Role"]["Arn"]


def create_basic_codepipeline(client, name):
    return client.create_pipeline(
        pipeline={
            "name": name,
            "roleArn": get_role_arn(),
            "artifactStore": {
                "type": "S3",
                "location": "codepipeline-us-east-1-123456789012",
            },
            "stages": [
                {
                    "name": "Stage-1",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Source",
                                "owner": "AWS",
                                "provider": "S3",
                                "version": "1",
                            },
                            "configuration": {
                                "S3Bucket": "test-bucket",
                                "S3ObjectKey": "test-object",
                            },
                            "outputArtifacts": [{"name": "artifact"},],
                        },
                    ],
                },
                {
                    "name": "Stage-2",
                    "actions": [
                        {
                            "name": "Action-1",
                            "actionTypeId": {
                                "category": "Approval",
                                "owner": "AWS",
                                "provider": "Manual",
                                "version": "1",
                            },
                        },
                    ],
                },
            ],
        },
        tags=[{"key": "key", "value": "value"}],
    )
