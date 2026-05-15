"""
Broadlink Device Patch — Config Flow
讓使用者可透過 HA 整合頁面（Settings → Devices & Services）安裝此整合，
不需要手動編輯 configuration.yaml。

Allows users to install this integration via the HA Integrations UI
(Settings → Devices & Services) without editing configuration.yaml.
"""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from . import (
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_MANUFACTURER,
    CONF_MODEL,
    DEFAULT_DEVICES,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    DOMAIN,
    _parse_device_id,
)

_LOGGER = logging.getLogger(__name__)


class BroadlinkPatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """處理初次安裝的 Config Flow。
    Handles the initial setup flow shown when the user adds the integration.
    """

    # Config Entry 的格式版本，未來若 options 結構改變可遞增
    # Version of the config entry format; increment if the options schema changes
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """使用者點擊「新增整合」後進入的第一個（也是唯一一個）步驟。
        The first (and only) step shown after the user clicks 'Add Integration'.

        此步驟不要求輸入任何欄位——按下送出即可完成安裝。
        No fields are required; just click Submit to complete installation.
        預設裝置（RM mini 3, 0x27C8）會在下次重啟時自動注入。
        The default device (RM mini 3, 0x27C8) will be patched in on next restart.
        """

        # 防止重複安裝：同一時間只允許一個 Config Entry
        # Prevent duplicate setup: only one Config Entry is allowed at a time
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # 使用者按下送出，建立 Config Entry（data 留空，裝置清單存在 options）
            # User clicked Submit — create the Config Entry (data empty, devices in options)
            return self.async_create_entry(
                title="Broadlink Device Patch",
                data={},
                # 預設裝置清單寫入 options，之後可透過 Options Flow 修改
                # Write the default device list to options; editable later via Options Flow
                options={CONF_DEVICES: DEFAULT_DEVICES},
            )

        # 尚未送出，顯示確認表單（無輸入欄位，只有說明文字）
        # Not yet submitted — show the confirmation form (description only, no input fields)
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """回傳 Options Flow 處理器，讓使用者日後可從整合頁面修改裝置清單。
        Return the Options Flow handler so users can edit the device list later
        from the integration's 'Configure' button.
        """
        return BroadlinkPatchOptionsFlow(config_entry)


class BroadlinkPatchOptionsFlow(config_entries.OptionsFlow):
    """處理「設定」按鈕的 Options Flow，讓使用者新增自訂裝置。
    Handles the 'Configure' button Options Flow for adding custom devices.

    目前提供單一裝置的新增表單；重複送出可累積多筆裝置。
    Currently provides a single-device add form; submit multiple times to add more.
    """

    def __init__(self, config_entry):
        """初始化，保存目前的 Config Entry 以便讀取現有 options。
        Initialise and store the current Config Entry to read existing options.
        """
        # 保存 Config Entry 供後續步驟使用
        # Store the Config Entry for use in subsequent steps
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Options Flow 的進入點，顯示新增裝置的表單。
        Entry point of the Options Flow — shows the add-device form.
        """
        errors = {}

        if user_input is not None:
            raw_id = user_input.get(CONF_DEVICE_ID, "").strip()

            # 驗證 device_id 格式
            # Validate the device_id format
            if _parse_device_id(raw_id) is None:
                errors[CONF_DEVICE_ID] = "invalid_device_id"
            else:
                # 讀取現有裝置清單並附加新裝置
                # Read the existing device list and append the new device
                existing = list(
                    self._config_entry.options.get(CONF_DEVICES, DEFAULT_DEVICES)
                )
                new_device = {
                    CONF_DEVICE_ID: raw_id,
                    CONF_MODEL: user_input.get(CONF_MODEL, DEFAULT_MODEL),
                    CONF_MANUFACTURER: user_input.get(
                        CONF_MANUFACTURER, DEFAULT_MANUFACTURER
                    ),
                }
                existing.append(new_device)

                _LOGGER.debug(
                    "Options updated: added device id=%s. Total devices: %d.",
                    raw_id,
                    len(existing),
                )

                # 儲存更新後的 options，HA 會在下次重啟時套用
                # Save the updated options; HA will apply them on next restart
                return self.async_create_entry(
                    title="", data={CONF_DEVICES: existing}
                )

        # 顯示新增裝置的輸入表單
        # Show the add-device input form
        schema = vol.Schema(
            {
                # 裝置 ID 為必填（例如 "0x27C8"）
                # Device ID is required (e.g. "0x27C8")
                vol.Required(CONF_DEVICE_ID): str,

                # 型號與製造商為選填，有預設值
                # Model and manufacturer are optional with defaults
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
                vol.Optional(
                    CONF_MANUFACTURER, default=DEFAULT_MANUFACTURER
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
