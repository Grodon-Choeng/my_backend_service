from typing import Optional

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import Field, ValidationError

from src.core.config import BaseSettings, refer_to_field


class TestConfig:
    class SampleSettings(BaseSettings):
        main_field: Optional[str] = Field(default="default_value")
        linked_field: Optional[str] = refer_to_field(refer_to="main_field")
        unlinked_field: Optional[str] = Field(default=None)
        another_field: Optional[str] = Field(default="default_another")

    def test_refer_to_field_with_value(self):
        """测试refer_to_field在有值时不引用其他字段"""
        settings = self.SampleSettings(main_field="custom", linked_field="explicit")
        assert settings.main_field == "custom"  # nosec
        assert settings.linked_field == "explicit"  # nosec

    def test_refer_to_field_without_value(self):
        """测试refer_to_field在无值时引用其他字段"""
        settings = self.SampleSettings(main_field="source_value")
        assert settings.linked_field == "source_value"  # nosec

    def test_refer_to_field_with_none(self):
        """测试refer_to_field在引用字段为None时的行为"""
        settings = self.SampleSettings(main_field=None)
        assert settings.linked_field is None  # nosec

    def test_unlinked_field(self):
        """测试未链接的字段不受影响"""
        settings = self.SampleSettings(unlinked_field="standalone")
        assert settings.unlinked_field == "standalone"  # nosec

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
        assert settings.main_field == "explicit_value"  # nosec
        # 环境变量次之
        settings = self.SampleSettings()
        assert settings.main_field == "env_value"
        # 最后是默认值
        monkeypatch.delenv("MAIN_FIELD")
        settings = self.SampleSettings()
        assert settings.main_field == "default_value"

    def test_invalid_reference(self):
        """测试引用不存在的字段"""

        class InvalidSettings(BaseSettings):
            bad_field: str = refer_to_field(refer_to="nonexistent_field")

        # Pydantic v2 doesn't raise ValidationError on definition, but on instantiation
        # when it can't find the referenced field to get a value from.
        # And since bad_field has no default, it will raise a validation error.
        with pytest.raises(ValidationError):
            InvalidSettings()

    def test_chained_references(self):
        """测试链式引用 (c -> b -> a)"""

        class ChainedSettings(BaseSettings):
            field_a: Optional[str] = "value_a"
            field_b: Optional[str] = refer_to_field(refer_to="field_a")
            field_c: Optional[str] = refer_to_field(refer_to="field_b")

        settings = ChainedSettings()
        assert settings.field_a == "value_a"
        assert settings.field_b == "value_a"
        assert settings.field_c == "value_a"

    def test_dotenv_loading(self, monkeypatch, tmp_path):
        """测试从 .env 文件加载"""
        # 创建一个临时的 .env 文件
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("MAIN_FIELD=dotenv_value")

        # 切换到临时目录，以便 Pydantic 能找到 .env 文件
        monkeypatch.chdir(tmp_path)

        # Set CONFIG_FILES to trigger the new logic
        monkeypatch.setenv("CONFIG_FILES", str(dotenv_file))

        settings = self.SampleSettings()
        assert settings.main_field == "dotenv_value"

    def test_multiple_config_files(self, monkeypatch, tmp_path):
        """测试加载多个配置文件，后面的覆盖前面的"""
        config1 = tmp_path / "config1.env"
        config1.write_text('MAIN_FIELD="file1"\nANOTHER_FIELD="file1_only"')

        config2 = tmp_path / "config2.env"
        config2.write_text('MAIN_FIELD="file2"')

        monkeypatch.setenv("CONFIG_FILES", f"{config1},{config2}")

        settings = self.SampleSettings()

        # config2 overrides config1
        assert settings.main_field == "file2"  # nosec
        # value from config1 is preserved
        assert settings.another_field == "file1_only"  # nosec

    def test_env_overrides_config_files(self, monkeypatch, tmp_path):
        """测试环境变量覆盖所有配置文件"""
        config1 = tmp_path / "config.env"
        config1.write_text('MAIN_FIELD="file_value"')

        monkeypatch.setenv("CONFIG_FILES", str(config1))
        monkeypatch.setenv("MAIN_FIELD", "env_value")

        settings = self.SampleSettings()
        assert settings.main_field == "env_value"

    def test_nonexistent_config_file(self, monkeypatch, tmp_path):
        """测试当配置文件不存在时，不应引发错误"""
        nonexistent_file = tmp_path / "nonexistent.env"
        monkeypatch.setenv("CONFIG_FILES", str(nonexistent_file))

        # Should not raise an error
        settings = self.SampleSettings()
        assert settings.main_field == "default_value"

    def test_default_dotenv_if_no_config_files(self, monkeypatch, tmp_path):
        """测试当CONFIG_FILES未设置时，回退到默认的.env加载"""
        # Clear CONFIG_FILES if it's set
        monkeypatch.delenv("CONFIG_FILES", raising=False)

        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("MAIN_FIELD=default_env_value")

        monkeypatch.chdir(tmp_path)

        settings = self.SampleSettings()
        assert settings.main_field == "default_env_value"  # nosec


@given(st.text(), st.one_of(st.none(), st.text()))
def test_property_based_refer_to_field(main_value, linked_value):
    """使用 Hypothesis 进行属性测试"""

    class PropSettings(BaseSettings):
        main_field: Optional[str]
        linked_field: Optional[str] = refer_to_field(refer_to="main_field")

    settings = PropSettings(main_field=main_value, linked_field=linked_value)

    if linked_value is not None:
        # 如果显式提供了值，则该值优先
        assert settings.linked_field == linked_value  # nosec
    else:
        # 否则，它应该引用 main_field 的值
        assert settings.linked_field == main_value  # nosec
