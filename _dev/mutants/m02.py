"""Wrong versions of the M02 snapshot — exact text edits applied to a copy of course_project/solutions/m02."""
NET = "infra/network.yaml"
MUTANTS = [
    {"id": "second-nat-in-lab", "edits": {NET: [["  NatGatewayB:\n    Type: AWS::EC2::NatGateway\n    Condition: IsProd\n",
                                                 "  NatGatewayB:\n    Type: AWS::EC2::NatGateway\n"]]}},
    {"id": "data-tier-to-nat", "edits": {NET: [["  PublicSubnetARoutes:", "  DataDefaultRoute:\n    Type: AWS::EC2::Route\n    Properties:\n"
                                                "      RouteTableId: !Ref DataRouteTable\n      DestinationCidrBlock: 0.0.0.0/0\n"
                                                "      NatGatewayId: !Ref NatGatewayA\n\n  PublicSubnetARoutes:"]]}},
    {"id": "app-open-to-vpc", "edits": {NET: [["SourceSecurityGroupId: !Ref AlbSecurityGroup}", "CidrIp: 10.20.0.0/16}"]]}},
    {"id": "ssh-from-anywhere", "edits": {NET: [["        - {IpProtocol: tcp, FromPort: 8000, ToPort: 8000, SourceSecurityGroupId: !Ref AlbSecurityGroup}",
                                                 "        - {IpProtocol: tcp, FromPort: 8000, ToPort: 8000, SourceSecurityGroupId: !Ref AlbSecurityGroup}\n"
                                                 "        - {IpProtocol: tcp, FromPort: 22, ToPort: 22, CidrIp: 0.0.0.0/0}"]]}},
    {"id": "s3-endpoint-misses-data", "edits": {NET: [["RouteTableIds: [!Ref AppRouteTableA, !Ref AppRouteTableB, !Ref DataRouteTable]\n      PolicyDocument",
                                                       "RouteTableIds: [!Ref AppRouteTableA, !Ref AppRouteTableB]\n      PolicyDocument"]]}},
    {"id": "endpoint-any-account", "edits": {NET: [["            Condition:\n              StringEquals: {'aws:ResourceAccount': !Ref 'AWS::AccountId'}\n", ""]]}},
    {"id": "logs-kept-forever", "edits": {NET: [["      RetentionInDays: 30\n", ""]]}},
    {"id": "flow-role-any-group", "edits": {NET: [["log-group:/${Prefix}/vpc-flow-logs:*'", "log-group:*'"]]}},
    {"id": "overlapping-subnets", "edits": {NET: [["CidrBlock: !Select [10, !Cidr [!Ref VpcCidr, 12, 8]]", "CidrBlock: !Select [9, !Cidr [!Ref VpcCidr, 12, 8]]"]]}},
    {"id": "plan-not-documented", "edits": {"README.md": [["## Network plan", "## Network"]]}},
]
