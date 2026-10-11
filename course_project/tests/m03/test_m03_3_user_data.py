"""M03.3 — user data that installs and starts the Shortly app."""
import pytest


@pytest.fixture
def script(user_data):
    return user_data("compute", "AppLaunchTemplate")


def test_starts_with_a_shebang(script):
    assert script.startswith("#!/bin/bash"), "UserData must begin with #!/bin/bash (cloud-init runs it as a script)"


def test_contains_the_whole_app(script, repo):
    app = repo / "app" / "app.py"
    assert app.exists(), "app/app.py is missing: run  python <course>/course_project/tools/start_milestone.py 3 --repo <your repo>"
    lines = [l for l in app.read_text(encoding="utf-8").splitlines() if l.strip()]
    present = set(script.splitlines())
    missing = [l for l in lines if l not in present]
    assert not missing, (f"UserData is missing {len(missing)} line(s) of app/app.py, first: {missing[0]!r}. Write the file with a "
                         "heredoc (cat > /opt/shortly/app.py <<'EOF' … EOF) and paste app.py between the markers, unchanged")


def test_runs_as_a_service(script):
    assert "systemctl enable --now shortly" in script, "start the app with systemctl enable --now shortly (so it also starts after a reboot)"
    assert "[Service]" in script and "ExecStart=" in script, "write /etc/systemd/system/shortly.service with a [Service] section and ExecStart="
    assert "PORT=8000" in script, "the unit needs Environment=PORT=8000: the target group sends traffic to port 8000"
    assert "Restart=always" in script, "add Restart=always so systemd restarts the app if it crashes"


def test_fits_the_user_data_limit(script):
    size = len(script.encode("utf-8"))
    assert size <= 16384, f"UserData is {size} bytes; EC2 allows 16 KB (16384) before base64. Keep the script small"
