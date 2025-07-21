from typing import Optional

import pytest
from pydantic import ValidationError,Field
from src.core.config import BaseSettings, refer_to_field


class TestConfig:
    class SampleSettings(BaseSettings):
        main_field: Optional[str] = Field(default="default_value")
        linked_field: Optional[str] = refer_to_field(refer_to="main_field")
        unlinked_field: Optional[str] = Field(default=None)

    def test_refer_to_field_with_value(self):
        """测试refer_to_field在有值时不引用其他字段"""
        settings = self.SampleSettings(main_field="custom", linked_field="explicit")
        assert settings.main_field == "custom"
        assert settings.linked_field == "explicit"

    def test_refer_to_field_without_value(self):
        """测试refer_to_field在无值时引用其他字段"""
        settings = self.SampleSettings(main_field="source_value")
        assert settings.linked_field == "source_value"

    def test_refer_to_field_with_none(self):
        """测试refer_to_field在引用字段为None时的行为"""
        settings = self.SampleSettings(main_field=None)
        assert settings.linked_field is None

    def test_unlinked_field(self):
        """测试未链接的字段不受影响"""
        settings = self.SampleSettings(unlinked_field="standalone")
        assert settings.unlinked_field == "standalone"

    def test_env_loading(self, monkeypatch):
        """测试环境变量加载"""
        monkeypatch.setenv("MAIN_FIELD", "env_value")
        settings = self.SampleSettings()
        assert settings.main_field == "env_value"

    def test_field_priority(self, monkeypatch):
        """测试字段优先级：显式值 > 环境变量 > 默认值"""
        monkeypatch.setenv("MAIN_FIELD", "env_value")
        # 显式值优先
        settings = self.SampleSettings(main_field="explicit_value")
        assert settings.main_field == "explicit_value"
        # 环境变量次之
        settings = self.SampleSettings()
        assert settings.main_field == "env_value"
        # 最后是默认值
        monkeypatch.delenv("MAIN_FIELD")
        settings = self.SampleSettings()
        assert settings.main_field == "default_value"

    def test_invalid_reference(self):
        """测试引用不存在的字段"""
        with pytest.raises(ValidationError):
            class InvalidSettings(BaseSettings):
                bad_field: str = refer_to_field(refer_to="nonexistent_field")

            InvalidSettings()
