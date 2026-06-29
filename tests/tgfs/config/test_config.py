import pytest
from tgfs.config import (
    WebDAVConfig,
    ManagerConfig,
    DownloadConfig,
    UserConfig,
    JWTConfig,
    ServerConfig,
    TGFSConfig,
    Config,
    GithubRepoConfig,
    MetadataConfig,
    MetadataType,
    MetadataConfigDict,
    _expand_env_vars,
    _load_dotenv,
)


class TestWebDAVConfig:
    def test_from_dict(self):
        data = {"host": "localhost", "port": 8080, "path": "/webdav"}
        config = WebDAVConfig.from_dict(data)

        assert config.host == "localhost"
        assert config.port == 8080
        assert config.path == "/webdav"


class TestManagerConfig:
    def test_from_dict(self):
        data = {"host": "0.0.0.0", "port": 9000}
        config = ManagerConfig.from_dict(data)

        assert config.host == "0.0.0.0"
        assert config.port == 9000


class TestDownloadConfig:
    def test_from_dict(self):
        data = {"chunk_size_kb": 1024}
        config = DownloadConfig.from_dict(data)

        assert config.chunk_size_kb == 1024


class TestUserConfig:
    def test_from_dict_readonly_false(self):
        data = {"password": "secret", "readonly": False}
        config = UserConfig.from_dict(data)

        assert config.password == "secret"
        assert config.readonly is False

    def test_from_dict_readonly_default_false(self):
        data = {"password": "secret"}
        config = UserConfig.from_dict(data)

        assert config.password == "secret"
        assert config.readonly is False

    def test_from_dict_readonly_true(self):
        data = {"password": "secret", "readonly": True}
        config = UserConfig.from_dict(data)

        assert config.password == "secret"
        assert config.readonly is True


class TestJWTConfig:
    def test_from_dict(self):
        data = {"secret": "jwt_secret", "algorithm": "HS256", "life": 3600}
        config = JWTConfig.from_dict(data)

        assert config.secret == "jwt_secret"
        assert config.algorithm == "HS256"
        assert config.life == 3600


class TestServerConfig:
    def test_from_dict(self):
        data = {"host": "127.0.0.1", "port": 8000}
        config = ServerConfig.from_dict(data)

        assert config.host == "127.0.0.1"
        assert config.port == 8000


class TestTGFSConfig:
    def test_from_dict_minimal(self):
        data = {
            "users": {},
            "download": {"chunk_size_kb": 512},
            "jwt": {"secret": "test", "algorithm": "HS256", "life": 1800},
            "server": {"host": "localhost", "port": 3000},
        }
        config = TGFSConfig.from_dict(data)

        assert config.users == {}
        assert config.download.chunk_size_kb == 512
        assert config.jwt.secret == "test"
        assert config.server.host == "localhost"

    def test_from_dict_with_users(self):
        data = {
            "users": {
                "admin": {"password": "admin123", "readonly": False},
                "viewer": {"password": "view123", "readonly": True},
            },
            "download": {"chunk_size_kb": 512},
            "jwt": {"secret": "test", "algorithm": "HS256", "life": 1800},
            "server": {"host": "localhost", "port": 3000},
        }
        config = TGFSConfig.from_dict(data)

        assert "admin" in config.users
        assert "viewer" in config.users
        assert config.users["admin"].password == "admin123"
        assert config.users["admin"].readonly is False
        assert config.users["viewer"].readonly is True

    def test_from_dict_no_users(self):
        data = {
            "users": None,
            "download": {"chunk_size_kb": 512},
            "jwt": {"secret": "test", "algorithm": "HS256", "life": 1800},
            "server": {"host": "localhost", "port": 3000},
        }
        config = TGFSConfig.from_dict(data)

        assert config.users == {}


class TestGithubRepoConfig:
    def test_from_dict(self):
        data = {"repo": "owner/repo", "commit": "main", "access_token": "token123"}
        config = GithubRepoConfig.from_dict(data)

        assert config.repo == "owner/repo"
        assert config.commit == "main"
        assert config.access_token == "token123"


class TestMetadataConfig:
    def test_from_dict_pinned_message(self):
        config = MetadataConfig.from_dict(
            MetadataConfigDict(type="pinned_message", name="name", github_repo=None)
        )

        assert config.type == MetadataType.PINNED_MESSAGE
        assert config.github_repo is None

    def test_from_dict_github_repo(self):
        config = MetadataConfig.from_dict(
            MetadataConfigDict(
                type="github_repo",
                name="name",
                github_repo={
                    "repo": "owner/repo",
                    "commit": "main",
                    "access_token": "token123",
                },
            )
        )

        assert config.type == MetadataType.GITHUB_REPO
        assert config.github_repo is not None
        assert config.github_repo.repo == "owner/repo"

    def test_from_dict_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown metadata type: unknown_type"):
            MetadataConfig.from_dict(
                MetadataConfigDict(type="unknown_type", name="name", github_repo=None)
            )


class TestConfig:
    def test_from_dict(self):
        data = {
            "telegram": {
                "api_id": 12345,
                "api_hash": "hash123",
                "bot": {"token": "bot_token", "session_file": "bot.session"},
                "account": {"session_file": "account.session"},
                "login_timeout": 30000,
                "private_file_channel": 123456,
                "public_file_channel": 654321,
            },
            "tgfs": {
                "users": {},
                "download": {"chunk_size_kb": 1024},
                "jwt": {"secret": "jwt_secret", "algorithm": "HS256", "life": 3600},
                "server": {"host": "0.0.0.0", "port": 8080},
            },
        }
        config = Config.from_dict(data)

        assert config.telegram.api_id == 12345
        assert config.tgfs.download.chunk_size_kb == 1024


class TestExpandEnvVars:
    def test_replaces_in_string(self, monkeypatch):
        monkeypatch.setenv("TG_BOT_TOKEN", "123:ABC")
        assert _expand_env_vars("${TG_BOT_TOKEN}") == "123:ABC"

    def test_leaves_plain_strings_untouched(self):
        assert _expand_env_vars("0.0.0.0") == "0.0.0.0"

    def test_recurses_into_dicts_and_lists(self, monkeypatch):
        monkeypatch.setenv("PAT", "github_pat_xyz")
        data = {"bot": {"tokens": ["${PAT}", "plain"]}}
        assert _expand_env_vars(data) == {
            "bot": {"tokens": ["github_pat_xyz", "plain"]}
        }

    def test_non_strings_pass_through(self):
        assert _expand_env_vars(12345) == 12345
        assert _expand_env_vars(True) is True

    def test_value_used_literally_not_as_regex_template(self, monkeypatch):
        # Secrets may contain $, \, } etc. - must not be treated as backrefs.
        monkeypatch.setenv("SECRET", r"a$b\1c}d")
        assert _expand_env_vars("${SECRET}") == r"a$b\1c}d"

    def test_missing_var_raises(self, monkeypatch):
        monkeypatch.delenv("DOES_NOT_EXIST", raising=False)
        with pytest.raises(ValueError, match="DOES_NOT_EXIST"):
            _expand_env_vars("${DOES_NOT_EXIST}")


class TestLoadDotenv:
    def test_missing_file_is_noop(self, tmp_path):
        _load_dotenv(str(tmp_path / "nope.env"))  # should not raise

    def test_loads_pairs_and_ignores_comments(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FOO", raising=False)
        monkeypatch.delenv("BAR", raising=False)
        env = tmp_path / ".env"
        env.write_text('# comment\nFOO=hello\nBAR="quoted value"\n\n')
        _load_dotenv(str(env))
        import os

        assert os.environ["FOO"] == "hello"
        assert os.environ["BAR"] == "quoted value"

    def test_existing_env_takes_precedence(self, tmp_path, monkeypatch):
        monkeypatch.setenv("FOO", "from_real_env")
        env = tmp_path / ".env"
        env.write_text("FOO=from_file\n")
        _load_dotenv(str(env))
        import os

        assert os.environ["FOO"] == "from_real_env"

    def test_value_with_equals_sign(self, tmp_path, monkeypatch):
        monkeypatch.delenv("JWT", raising=False)
        env = tmp_path / ".env"
        env.write_text("JWT=a=b=c\n")
        _load_dotenv(str(env))
        import os

        assert os.environ["JWT"] == "a=b=c"


class TestConfigFunctions:
    def test_get_config_loads_file(self, mocker):
        mock_open = mocker.patch("tgfs.config.open")
        mock_yaml_load = mocker.patch("tgfs.config.yaml.safe_load")
        mocker.patch("tgfs.config._load_dotenv")  # isolate from .env loading
        mocker.patch("tgfs.config.__config", None)
        from tgfs.config import get_config

        mock_yaml_load.return_value = {
            "telegram": {
                "api_id": 12345,
                "api_hash": "hash123",
                "bot": {"token": "bot_token", "session_file": "bot.session"},
                "account": {"session_file": "account.session"},
                "login_timeout": 30000,
                "private_file_channel": 123456,
                "public_file_channel": 654321,
            },
            "tgfs": {
                "users": {},
                "download": {"chunk_size_kb": 1024},
                "jwt": {"secret": "jwt_secret", "algorithm": "HS256", "life": 3600},
                "server": {"host": "0.0.0.0", "port": 8080},
            },
        }

        config = get_config()

        mock_open.assert_called_once()
        mock_yaml_load.assert_called_once()
        assert config.telegram.api_id == 12345
