import pytest

from _harness.awslib import cfn

NETWORK = """AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  Prefix: {Type: String, Default: shortly}
  Env: {Type: String, AllowedValues: [lab, prod]}
  VpcCidr: {Type: String, Default: 10.20.0.0/16}
Conditions:
  IsProd: !Equals [!Ref Env, prod]
  IsLab: !Not [!Condition IsProd]
  ProdInUsEast1: !And [!Condition IsProd, !Equals [!Ref 'AWS::Region', us-east-1]]
  Either: !Or [!Condition IsLab, !Condition ProdInUsEast1]
Resources:
  Vpc:
    Type: AWS::EC2::VPC
    Properties: {CidrBlock: !Ref VpcCidr}
  SubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Select [0, !Cidr [!Ref VpcCidr, 6, 8]]
  SubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref Vpc
      AvailabilityZone: !Select [1, !GetAZs {Ref: 'AWS::Region'}]
      CidrBlock: !Select [1, !Cidr [!Ref VpcCidr, 6, 8]]
  NatA:
    Type: AWS::EC2::NatGateway
    Properties: {SubnetId: !Ref SubnetA}
  NatB:
    Type: AWS::EC2::NatGateway
    Condition: IsProd
    Properties: {SubnetId: !Ref SubnetB}
  RouteB:
    Type: AWS::EC2::Route
    Properties:
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !If [IsProd, !Ref NatB, !Ref NatA]
      Description: !If [IsProd, per-az, !Ref 'AWS::NoValue']
      Tags: [{Key: a, Value: b}, !If [IsProd, {Key: env, Value: prod}, !Ref 'AWS::NoValue']]
Outputs:
  AppSubnets:
    Value: !Join [',', [!Ref SubnetA, !Ref SubnetB]]
  Imported:
    Value: !ImportValue {'Fn::Sub': '${Prefix}-vpc-id'}
"""


@pytest.fixture(scope="module")
def template():
    return cfn.load_template_text(NETWORK)


def test_conditions(template):
    assert cfn.evaluate_conditions(template, {"Env": "prod"}) == {"IsProd": True, "IsLab": False,
                                                                  "ProdInUsEast1": True, "Either": True}
    assert cfn.evaluate_conditions(template, {"Env": "lab"}) == {"IsProd": False, "IsLab": True,
                                                                 "ProdInUsEast1": False, "Either": True}
    assert cfn.evaluate_conditions(template, {"Env": "prod"}, {"AWS::Region": "eu-west-1"})["Either"] is False


def test_bad_conditions():
    with pytest.raises(cfn.TemplateError, match="unknown condition"):
        cfn.evaluate_conditions({"Conditions": {"A": {"Condition": "Missing"}}})
    with pytest.raises(cfn.TemplateError, match="itself"):
        cfn.evaluate_conditions({"Conditions": {"A": {"Condition": "A"}}})


def test_select_getazs_and_cidr(template):
    res = cfn.active_resources(template, {"Prefix": "shortly", "Env": "prod", "VpcCidr": "10.20.0.0/16"})
    assert res["SubnetA"]["Properties"]["AvailabilityZone"] == "us-east-1a"
    assert res["SubnetB"]["Properties"]["AvailabilityZone"] == "us-east-1b"
    assert res["SubnetA"]["Properties"]["CidrBlock"] == "10.20.0.0/24"
    assert res["SubnetB"]["Properties"]["CidrBlock"] == "10.20.1.0/24"
    assert cfn.render({"Fn::Cidr": ["10.0.0.0/16", 3, 12]}) == ["10.0.0.0/20", "10.0.16.0/20", "10.0.32.0/20"]
    assert cfn.render({"Fn::GetAZs": "eu-west-1"})[:2] == ["eu-west-1a", "eu-west-1b"]


def test_select_out_of_range():
    with pytest.raises(cfn.TemplateError, match="Fn::Select"):
        cfn.render({"Fn::Select": [9, ["a", "b"]]})


def test_condition_on_resource_and_if(template):
    prod = cfn.active_resources(template, {"Env": "prod"})
    lab = cfn.active_resources(template, {"Env": "lab"})
    assert "NatB" in prod and "NatB" not in lab
    assert prod["RouteB"]["Properties"]["NatGatewayId"] == "NatB"
    assert lab["RouteB"]["Properties"]["NatGatewayId"] == "NatA"


def test_novalue_drops_properties_and_items(template):
    prod = cfn.active_resources(template, {"Env": "prod"})["RouteB"]["Properties"]
    lab = cfn.active_resources(template, {"Env": "lab"})["RouteB"]["Properties"]
    assert prod["Description"] == "per-az" and "Description" not in lab
    assert prod["Tags"] == [{"Key": "a", "Value": "b"}, {"Key": "env", "Value": "prod"}]
    assert lab["Tags"] == [{"Key": "a", "Value": "b"}]
    assert cfn.render({"Ref": "AWS::NoValue"}) is None


def test_if_needs_conditions():
    with pytest.raises(cfn.TemplateError, match="evaluate_conditions"):
        cfn.render({"Fn::If": ["IsProd", "a", "b"]})


def test_join_of_refs_and_import_value(template):
    outputs = cfn.render(template["Outputs"], {"Prefix": "shortly"}, conditions={})
    assert outputs["AppSubnets"]["Value"] == "SubnetA,SubnetB"
    assert outputs["Imported"]["Value"] == "import:shortly-vpc-id"


def test_parameter_defaults_fill_in(template):
    assert cfn.parameter_values(template, {"Env": "lab"}) == {"Prefix": "shortly", "VpcCidr": "10.20.0.0/16", "Env": "lab"}
    res = cfn.active_resources(template, {"Env": "lab", "VpcCidr": "10.99.0.0/16"})
    assert res["Vpc"]["Properties"]["CidrBlock"] == "10.99.0.0/16"


def test_inline_functions_replaces_only_named(template):
    flat = cfn.inline_functions(template, {"Fn::Cidr"}, {"Env": "lab"})
    cidr_block = flat["Resources"]["SubnetA"]["Properties"]["CidrBlock"]
    assert cidr_block == {"Fn::Select": [0, ["10.20.0.0/24", "10.20.1.0/24", "10.20.2.0/24", "10.20.3.0/24",
                                             "10.20.4.0/24", "10.20.5.0/24"]]}
    assert flat["Resources"]["Vpc"]["Properties"]["CidrBlock"] == {"Ref": "VpcCidr"}


def test_base64_renders_unencoded_input():
    assert cfn.render({"Fn::Base64": {"Fn::Sub": "#!/bin/bash\necho ${Prefix}"}}, {"Prefix": "shortly"}) == "#!/bin/bash\necho shortly"


def test_split_of_join_and_import_value():
    joined = {"Fn::Join": [",", ["a", "b", "c"]]}
    assert cfn.render({"Fn::Split": [",", joined]}) == ["a", "b", "c"]
    assert cfn.render({"Fn::Split": [",", {"Fn::ImportValue": "name"}]}) == ["import:name"]
    assert cfn.render({"Fn::Select": [1, {"Fn::Split": ["-", "x-y-z"]}]}) == "y"


def test_split_of_a_list_is_an_error():
    with pytest.raises(cfn.TemplateError, match="Fn::Split"):
        cfn.render({"Fn::Split": [",", ["a", "b"]]})


MAPPED = """AWSTemplateFormatVersion: '2010-09-09'
Mappings:
  Elb:
    us-east-1: {Account: '127311923021'}
    eu-west-1: {Account: '156460612806'}
Resources:
  Policy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: b
      PolicyDocument:
        Principal: {AWS: !Join [':', [arn, !FindInMap [Elb, !Ref 'AWS::Region', Account]]]}
Outputs:
  Acct:
    Value: !FindInMap [Elb, us-east-1, Account]
"""


def test_find_in_map_renders_with_template_mappings():
    tpl = cfn.load_template_text(MAPPED)
    res = cfn.active_resources(tpl, {}, {"AWS::Region": "eu-west-1"})
    assert res["Policy"]["Properties"]["PolicyDocument"]["Principal"]["AWS"] == "arn:156460612806"
    assert cfn.render(tpl["Outputs"], {}, None, {}, tpl["Mappings"]) == {"Acct": {"Value": "127311923021"}}


def test_find_in_map_missing_key_is_an_error():
    tpl = cfn.load_template_text(MAPPED)
    with pytest.raises(cfn.TemplateError, match="FindInMap"):
        cfn.active_resources(tpl, {}, {"AWS::Region": "ap-south-1"})
    with pytest.raises(cfn.TemplateError, match="FindInMap"):
        cfn.render({"Fn::FindInMap": ["Nope", "a", "b"]})


def test_render_mappings_do_not_leak_between_calls():
    tpl = cfn.load_template_text(MAPPED)
    assert cfn.render({"Fn::FindInMap": ["Elb", "us-east-1", "Account"]}, {}, None, {}, tpl["Mappings"]) == "127311923021"
    with pytest.raises(cfn.TemplateError):
        cfn.render({"Fn::FindInMap": ["Elb", "us-east-1", "Account"]})


MOTO = """AWSTemplateFormatVersion: '2010-09-09'
Resources:
  Cache:
    Type: AWS::ElastiCache::ReplicationGroup
    Properties: {ReplicationGroupDescription: x}
  Database:
    Type: AWS::RDS::DBInstance
    Properties: {Engine: postgres}
  Reader:
    Type: AWS::IAM::Policy
    DependsOn: [Cache, Database]
    Properties:
      PolicyDocument:
        Statement:
          - Resource: !GetAtt Database.MasterUserSecret.SecretArn
          - Resource: !Sub '${Database.Endpoint.Address}/x'
Outputs:
  Secret: {Value: !GetAtt Database.MasterUserSecret.SecretArn}
  Address: {Value: !GetAtt Database.Endpoint.Address}
  CacheAddress: {Value: !GetAtt Cache.PrimaryEndPoint.Address}
  CacheName: {Value: !Ref Cache}
"""
SECRET = {"Database.MasterUserSecret.SecretArn": "arn:aws:secretsmanager:us-east-1:111122223333:secret:rds!db-moto"}


def test_for_moto_removes_types_outputs_and_replaces_getatt():
    tpl = cfn.load_template_text(MOTO)
    out = cfn.for_moto(tpl, {"AWS::ElastiCache::ReplicationGroup"}, SECRET)
    assert set(out["Resources"]) == {"Database", "Reader"}
    assert out["Resources"]["Reader"]["DependsOn"] == ["Database"]
    assert out["Resources"]["Reader"]["Properties"]["PolicyDocument"]["Statement"][0]["Resource"] == SECRET["Database.MasterUserSecret.SecretArn"]
    assert out["Resources"]["Reader"]["Properties"]["PolicyDocument"]["Statement"][1]["Resource"] == {"Fn::Sub": "${Database.Endpoint.Address}/x"}
    assert set(out["Outputs"]) == {"Address"}
    assert "Cache" in tpl["Resources"], "the original template is not changed"


def test_for_moto_without_getatt_values_only_drops_types():
    out = cfn.for_moto(cfn.load_template_text(MOTO), ["AWS::ElastiCache::ReplicationGroup"])
    assert "Fn::GetAtt" in str(out["Resources"]["Reader"]) and set(out["Outputs"]) == {"Secret", "Address"}


def test_for_moto_names_a_resource_that_still_uses_a_removed_one():
    tpl = cfn.load_template_text(MOTO.replace("Resource: !Sub '${Database.Endpoint.Address}/x'", "Resource: !Ref Cache"))
    with pytest.raises(cfn.TemplateError, match="Reader.*Cache|Cache.*Reader"):
        cfn.for_moto(tpl, {"AWS::ElastiCache::ReplicationGroup"}, SECRET)
    sub = cfn.load_template_text(MOTO.replace("${Database.Endpoint.Address}/x", "${Cache.PrimaryEndPoint.Address}"))
    with pytest.raises(cfn.TemplateError, match="Cache"):
        cfn.for_moto(sub, {"AWS::ElastiCache::ReplicationGroup"}, SECRET)
