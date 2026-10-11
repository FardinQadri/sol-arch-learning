"""M05.1 — the PostgreSQL database: parameters, the subnet group, and an instance that is private, encrypted and has no password in the template."""


def database(resources, **params):
    res = resources("data", **params)
    assert res.get("Database", {}).get("Type") == "AWS::RDS::DBInstance", "add Database (AWS::RDS::DBInstance) to infra/data.yaml"
    return res["Database"]["Properties"]


def test_parameters(template):
    params = template("data").get("Parameters", {})
    assert params.get("Prefix", {}).get("Default") == "shortly", "Parameter Prefix (String, Default shortly)"
    assert sorted(params.get("Env", {}).get("AllowedValues", [])) == ["lab", "prod"], "Parameter Env with AllowedValues [lab, prod]"
    assert "IsProd" in (template("data").get("Conditions") or {}), "add Condition IsProd: !Equals [!Ref Env, prod]; prod and lab differ in size, Multi-AZ, backups and protection"


def test_subnet_group_uses_the_data_subnets(resources, template):
    res = resources("data")
    group = res.get("DbSubnetGroup", {})
    assert group.get("Type") == "AWS::RDS::DBSubnetGroup", "add DbSubnetGroup (AWS::RDS::DBSubnetGroup): it tells RDS which subnets (so which Availability Zones) the database may use"
    props = group["Properties"]
    assert props.get("DBSubnetGroupDescription"), "DbSubnetGroup needs a DBSubnetGroupDescription"
    assert props.get("SubnetIds") == ["import:shortly-data-subnet-ids"], \
        "DbSubnetGroup SubnetIds: !Split [',', !ImportValue {'Fn::Sub': '${Prefix}-data-subnet-ids'}] (the M02 data subnets have no route to the internet)"
    raw = template("data")["Resources"]["DbSubnetGroup"]["Properties"]["SubnetIds"]
    assert "Fn::Split" in raw, "the exported subnet ids are one comma separated string: wrap the import in !Split [',', …]"


def test_engine_and_version(resources):
    p = database(resources)
    assert p.get("Engine") == "postgres", f"Engine is {p.get('Engine')!r}; use postgres (Shortly's links and users are relational and need transactions)"
    version = str(p.get("EngineVersion", ""))
    assert version.startswith("17."), f"EngineVersion is {version!r}; use a current 17.x release (the course solution uses '17.9'). Quote it so YAML keeps it a string"


def test_instance_class_follows_the_environment(resources):
    assert database(resources, Env="prod").get("DBInstanceClass") == "db.m7g.large", "prod DBInstanceClass: db.m7g.large (Graviton, 2 vCPU, 8 GiB)"
    assert database(resources, Env="lab").get("DBInstanceClass") == "db.t4g.micro", "lab DBInstanceClass: db.t4g.micro (the cheapest class, burstable). Use !If [IsProd, db.m7g.large, db.t4g.micro]"


def test_storage_is_gp3_20gib_on_port_5432(resources):
    p = database(resources)
    assert int(p.get("AllocatedStorage", 0)) == 20, f"AllocatedStorage is {p.get('AllocatedStorage')!r}; use 20 (GiB), the gp3 minimum"
    assert p.get("StorageType") == "gp3", f"StorageType is {p.get('StorageType')!r}; use gp3 (cheaper than gp2 and 3,000 IOPS included)"
    assert int(p.get("Port", 0)) == 5432, "set Port: 5432 explicitly so the endpoint port is the PostgreSQL port (the DB security group allows 5432 only)"


def test_storage_is_encrypted(resources):
    assert database(resources).get("StorageEncrypted") is True, \
        "set StorageEncrypted: true. Encryption can only be chosen when a database is created (you cannot encrypt an existing one in place), and it also encrypts backups, snapshots and replicas"


def test_the_password_is_managed_by_rds(resources):
    p = database(resources)
    assert p.get("MasterUsername") == "shortly", "MasterUsername: shortly"
    assert "MasterUserPassword" not in p, \
        "remove MasterUserPassword: a password in the template ends up in git and in CloudFormation. Use ManageMasterUserPassword: true instead"
    assert p.get("ManageMasterUserPassword") is True, \
        "set ManageMasterUserPassword: true. RDS then creates the master password in AWS Secrets Manager and can rotate it; no human or template ever sees it"


def test_the_database_is_private(resources):
    p = database(resources)
    assert p.get("PubliclyAccessible") is False, \
        "set PubliclyAccessible: false. A database in the data subnets has no internet route anyway, but a public address would be one misplaced security-group rule away from exposure"


def test_subnet_group_and_security_group(resources):
    p = database(resources)
    assert p.get("DBSubnetGroupName") == "DbSubnetGroup", "Database DBSubnetGroupName: !Ref DbSubnetGroup"
    assert p.get("VPCSecurityGroups") == ["import:shortly-db-sg-id"], \
        "Database VPCSecurityGroups: [!ImportValue {'Fn::Sub': '${Prefix}-db-sg-id'}]. The M02 database security group lets only the app tier reach port 5432; without it RDS attaches the VPC's default group"
