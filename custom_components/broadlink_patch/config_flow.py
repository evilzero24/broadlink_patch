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
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

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

# 操作選項常數 / Action option constants
_ACTION_ADD = "add"
_ACTION_REMOVE = "remove"


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


class BroadlinkPatchOptionsFlow(config_entries.OptionsFlowWithConfigEntry):
    """處理「設定」按鈕的 Options Flow，讓使用者管理自訂裝置清單。
    Handles the 'Configure' button Options Flow for managing the custom device list.

    使用 OptionsFlowWithConfigEntry，self.config_entry 由父類別自動提供。
    Uses OptionsFlowWithConfigEntry; self.config_entry is provided by the parent class.
    """

    async def async_step_init(self, user_input=None):
        """步驟一：顯示目前裝置清單，讓使用者選擇新增或移除。
        Step 1: Show current device list and let the user choose to add or remove.
        """
        existing = self.config_entry.options.get(CONF_DEVICES, DEFAULT_DEVICES)

        if user_input is not None:
            action = user_input.get("action")
            if action == _ACTION_ADD:
                return await self.async_step_add()
            if action == _ACTION_REMOVE:
                return await self.async_step_remove()

        # 將目前裝置清單格式化為說明文字中的佔位符
        # Format the current device list for the description placeholder
        lines = [
            f"• {d.get(CONF_MODEL, DEFAULT_MODEL)} ({d[CONF_DEVICE_ID]})"
            for d in existing
        ]
        devices_str = "\n".join(lines) if lines else "(無 / none)"

        schema = vol.Schema(
            {
                vol.Required("action", default=_ACTION_ADD): vol.In(
                    {
                        _ACTION_ADD: "新增裝置 / Add device",
                        _ACTION_REMOVE: "移除裝置 / Remove device",
                    }
                )
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={"devices": devices_str},
        )

    async def async_step_add(self, user_input=None):
        """步驟二（新增）：輸入新裝置的詳細資訊。
        Step 2 (add): Enter details for a new device.
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
                    self.config_entry.options.get(CONF_DEVICES, DEFAULT_DEVICES)
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

                return self.async_create_entry(title="", data={CONF_DEVICES: existing})

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): str,
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
                vol.Optional(CONF_MANUFACTURER, default=DEFAULT_MANUFACTURER): str,
            }
        )

        return self.async_show_form(
            step_id="add",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_remove(self, user_input=None):
        """步驟二（移除）：從清單中選取要刪除的裝置。
        Step 2 (remove): Select devices to delete from the list.
        """
        existing = list(self.config_entry.options.get(CONF_DEVICES, DEFAULT_DEVICES))

        if not existing:
            # 清單是空的，沒有東西可以移除
            # Nothing to remove — abort with a friendly message
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            remove_ids = set(user_input.get("remove_ids", []))
            updated = [d for d in existing if d[CONF_DEVICE_ID] not in remove_ids]

            _LOGGER.debug(
                "Options updated: removed %d device(s). Remaining: %d.",
                len(remove_ids),
                len(updated),
            )

            return self.async_create_entry(title="", data={CONF_DEVICES: updated})

        # 用多選清單讓使用者選取要刪除的裝置
        # Use a multi-select list so users can pick devices to delete
        schema = vol.Schema(
            {
                vol.Required("remove_ids"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {
                                "value": d[CONF_DEVICE_ID],
                                "label": f"{d.get(CONF_MODEL, DEFAULT_MODEL)} ({d[CONF_DEVICE_ID]})",
                            }
                            for d in existing
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )

        return self.async_show_form(step_id="remove", data_schema=schema)

