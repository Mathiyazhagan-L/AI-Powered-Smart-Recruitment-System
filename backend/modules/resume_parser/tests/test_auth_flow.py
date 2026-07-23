from modules.resume_parser.config import Settings
from modules.resume_parser.auth.service import AuthService


def test_otp_login_flow(tmp_path):
    settings = Settings(local_db_path=tmp_path / "auth.db", jwt_secret="test-secret")
    service = AuthService(settings)

    sent = service.send_otp("email", "Student@Example.com")
    assert sent["target"] == "student@example.com"

    otp = service.last_otp()
    verified = service.verify_otp("email", "Student@Example.com", otp["code"], "candidate")

    assert verified["access_token"]
    assert verified["user"]["role"] == "candidate"
    assert verified["user"]["email"] == "student@example.com"

    current_user = service.get_current_user(verified["access_token"])
    assert current_user["email"] == "student@example.com"
