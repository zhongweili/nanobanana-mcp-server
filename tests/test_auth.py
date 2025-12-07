import os
import pytest
from unittest.mock import MagicMock, patch

from nanobanana_mcp_server.config.settings import ServerConfig, AuthMethod, GeminiConfig
from nanobanana_mcp_server.services.gemini_client import GeminiClient
from nanobanana_mcp_server.core.exceptions import ADCConfigurationError

class TestAuthConfiguration:
    def test_api_key_auth_requires_api_key(self):
        """API Key認証時はAPI Keyが必須"""
        # API Keyがない状態を作る
        with patch.dict(os.environ, {}, clear=True):
            os.environ["NANOBANANA_AUTH_METHOD"] = "api_key"
            with pytest.raises(ValueError):
                ServerConfig.from_env()

    def test_vertex_ai_auth_requires_project(self):
        """Vertex AI認証時はプロジェクトIDが必須"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["NANOBANANA_AUTH_METHOD"] = "vertex_ai"
            with pytest.raises(ADCConfigurationError):
                ServerConfig.from_env()

    def test_auto_selects_api_key_when_available(self):
        """AUTOモードでAPI Keyがあればそれを使用"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["GEMINI_API_KEY"] = "test-key"
            config = ServerConfig.from_env()
            assert config.auth_method == AuthMethod.API_KEY

    def test_auto_selects_vertex_ai_when_no_api_key(self):
        """AUTOモードでAPI KeyがなければVertex AIを使用"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["GCP_PROJECT_ID"] = "test-project"
            config = ServerConfig.from_env()
            assert config.auth_method == AuthMethod.VERTEX_AI

    def test_auto_fails_when_no_auth_configured(self):
        """AUTOモードで認証情報がなければエラー"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                ServerConfig.from_env()

class TestGeminiClientAuth:
    @patch("google.genai.Client")
    def test_api_key_client_creation(self, mock_client_cls):
        """API Key認証でクライアントが正しく作成される"""
        config = ServerConfig(
            gemini_api_key="test-key",
            auth_method=AuthMethod.API_KEY
        )
        gemini_config = GeminiConfig()
        client = GeminiClient(config, gemini_config)
        
        # clientプロパティにアクセスして初期化
        _ = client.client
        
        mock_client_cls.assert_called_with(api_key="test-key")

    @patch("google.genai.Client")
    def test_vertex_ai_client_creation(self, mock_client_cls):
        """Vertex AI認証でクライアントが正しく作成される"""
        config = ServerConfig(
            gemini_api_key=None,
            auth_method=AuthMethod.VERTEX_AI,
            gcp_project_id="test-project",
            gcp_region="us-central1"
        )
        gemini_config = GeminiConfig()
        client = GeminiClient(config, gemini_config)
        
        # clientプロパティにアクセスして初期化
        _ = client.client
        
        mock_client_cls.assert_called_with(
            vertexai=True,
            project="test-project",
            location="us-central1"
        )
