import tomllib
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import (BaseSettings, DotEnvSettingsSource,
                               PydanticBaseSettingsSource)

from .exceptions import TomlSettingsError


class TomlConfigSettingsSource(PydanticBaseSettingsSource):
    def __init__(
        self,
        settings_cls: type[BaseSettings],
        dotenv_settings: PydanticBaseSettingsSource,
    ):
        self.settings_cls = settings_cls
        self.config = settings_cls.model_config
        self.dotenv_settings = dotenv_settings

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        env_file = self.config.get("env_file")
        if isinstance(self.dotenv_settings, DotEnvSettingsSource):
            env_file = env_file if env_file else self.dotenv_settings.env_file
        if not env_file:
            raise TomlSettingsError("No toml env_file")
        try:
            with open(env_file, "rb") as ft:  # type: ignore [arg-type]
                file_content_toml = tomllib.load(ft)
                field_value = file_content_toml.get(field_name)
                return field_value, field_name, False
        except Exception as e:
            raise TomlSettingsError(f"Error on open f{env_file}: {e}") from e

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(field, field_name)
            field_value = self.prepare_field_value(field_name, field, field_value, value_is_complex)
            if field_value is not None:
                d[field_key] = field_value

        return d
