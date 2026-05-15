"""
Broadlink Device Patch — Home Assistant 自訂整合
Broadlink Device Patch — Custom Integration for Home Assistant

將使用者自訂的裝置 ID 動態注入 broadlink Python 函式庫的 SUPPORTED_TYPES 字典，
使原本不在官方支援清單中的硬體設備也能被 HA 識別與使用。

Dynamically injects user-defined device IDs into the broadlink Python library's
SUPPORTED_TYPES registry, enabling hardware not listed in the official support
table to be recognised by Home Assistant.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
設定範例 / Configuration example (configuration.yaml):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  broadlink_patch:
    devices:
      - device_id: "0x27C8"   # 裝置型別 ID（十六進位）/ Device type ID (hex)
        model: "RM mini 3"    # 型號名稱 / Model name
        manufacturer: "Broadlink"  # 製造商 / Manufacturer
      - device_id: "0x5F36"
        model: "RM4 mini"
        manufacturer: "Broadlink"

若未填寫 devices，預設會注入 0x27C8 / RM mini 3。
If devices is omitted, 0x27C8 / RM mini 3 will be injected by default.
"""

import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

# 取得以模組名稱命名的 logger，方便在 HA 日誌中過濾
# Obtain a logger named after this module for easy filtering in HA logs
_LOGGER = logging.getLogger(__name__)

# 整合的唯一網域名稱，必須與目錄名稱相同
# Unique domain name for this integration; must match the directory name
DOMAIN = "broadlink_patch"

# ── 設定檔鍵名常數 / Configuration key constants ──────────────────────────────

CONF_DEVICES = "devices"        # 裝置清單鍵名 / Key for the list of devices
CONF_DEVICE_ID = "device_id"    # 裝置 ID 鍵名 / Key for device type ID
CONF_MODEL = "model"            # 型號鍵名 / Key for model name
CONF_MANUFACTURER = "manufacturer"  # 製造商鍵名 / Key for manufacturer name

# ── 預設值 / Default values ───────────────────────────────────────────────────

DEFAULT_MANUFACTURER = "Broadlink"  # 未指定時使用的預設製造商 / Fallback manufacturer
DEFAULT_MODEL = "Unknown"           # 未指定時使用的預設型號 / Fallback model name

# 未在 configuration.yaml 提供 devices 時，自動注入此預設裝置
# This device is injected automatically when no devices list is provided
DEFAULT_DEVICES = [
    {
        CONF_DEVICE_ID: "0x27C8",          # RM mini 3 的裝置型別 ID / RM mini 3 type ID
        CONF_MODEL: "RM mini 3",
        CONF_MANUFACTURER: DEFAULT_MANUFACTURER,
    }
]

# ── 設定驗證 Schema / Configuration validation schemas ────────────────────────

# 單一裝置項目的驗證規則
# Validation rules for a single device entry
_DEVICE_SCHEMA = vol.Schema(
    {
        # device_id 為必填欄位，必須是字串（例如 "0x27C8"）
        # device_id is required and must be a string (e.g. "0x27C8")
        vol.Required(CONF_DEVICE_ID): cv.string,

        # model 可選，未填則使用 DEFAULT_MODEL
        # model is optional; defaults to DEFAULT_MODEL if omitted
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,

        # manufacturer 可選，未填則使用 DEFAULT_MANUFACTURER
        # manufacturer is optional; defaults to DEFAULT_MANUFACTURER if omitted
        vol.Optional(CONF_MANUFACTURER, default=DEFAULT_MANUFACTURER): cv.string,
    }
)

# 整個整合的頂層設定驗證規則
# Top-level configuration validation for the entire integration
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                # devices 可選；若省略則使用 DEFAULT_DEVICES
                # devices is optional; falls back to DEFAULT_DEVICES when absent
                vol.Optional(CONF_DEVICES, default=DEFAULT_DEVICES): vol.All(
                    cv.ensure_list,   # 允許單一物件或清單 / Accept a single dict or a list
                    [_DEVICE_SCHEMA], # 對清單中每個項目套用 _DEVICE_SCHEMA / Validate each item
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,  # 允許其他整合的設定共存 / Allow other integrations' config keys
)


def _parse_device_id(raw: str | int) -> int | None:
    """將裝置 ID 字串或整數轉換為 Python int。
    Convert a device ID string or integer to a Python int.

    支援格式 / Supported formats:
      - "0x27C8"  （十六進位字串，大小寫均可 / hex string, case-insensitive）
      - "10184"   （十進位字串 / decimal string）
      - 10184     （Python 整數 / Python integer）

    回傳 None 表示無法解析。
    Returns None if the value cannot be parsed.
    """
    # 若已是整數，直接回傳，不需轉換
    # Already an integer — return as-is
    if isinstance(raw, int):
        return raw

    # 去除前後空白，避免使用者不小心多打空格
    # Strip surrounding whitespace to tolerate accidental spaces
    raw = raw.strip()

    try:
        # int(x, 0) 可自動辨識 0x 前綴（hex）或純數字（decimal）
        # int(x, 0) auto-detects 0x prefix (hex) or plain digits (decimal)
        return int(raw, 0)
    except ValueError:
        # 無法解析時回傳 None，由呼叫端決定如何處理
        # Return None on failure; the caller decides how to handle it
        return None


async def _do_patch(devices: list) -> bool:
    """核心修補邏輯，供 YAML 和 Config Entry 兩種啟動路徑共用。
    Core patching logic shared by both the YAML and Config Entry setup paths.
    """

    # ── 步驟 1：匯入 broadlink 函式庫 / Step 1: Import broadlink library ────────
    try:
        import broadlink  # noqa: PLC0415  # 延遲匯入以符合 HA 慣例 / Deferred import per HA convention
    except ImportError:
        # broadlink 函式庫不存在，無法繼續
        # broadlink library not found; cannot proceed
        _LOGGER.error(
            "Failed to import the broadlink Python library. "
            "Make sure the 'broadlink' integration is installed."
        )
        return False

    # ── 步驟 2：確認 SUPPORTED_TYPES 存在 / Step 2: Confirm SUPPORTED_TYPES exists ─
    # 不同版本的 broadlink 函式庫結構可能不同，需先確認屬性存在
    # Different library versions may have different structures; verify before use
    if not hasattr(broadlink, "SUPPORTED_TYPES"):
        _LOGGER.error(
            "broadlink.SUPPORTED_TYPES not found. "
            "The installed version of the broadlink library may be incompatible."
        )
        return False

    # 計數器：成功注入數 / 已存在跳過數
    # Counters: successfully injected / already existed and skipped
    injected = 0
    skipped = 0

    # ── 步驟 3：逐一處理裝置 / Step 3: Process each device entry ─────────────────
    for entry in devices:
        raw_id = entry[CONF_DEVICE_ID]

        # 將字串 ID（例如 "0x27C8"）轉換為整數
        # Convert string ID (e.g. "0x27C8") to an integer
        device_id = _parse_device_id(raw_id)

        # 若轉換失敗，記錄警告並跳過此項目
        # If conversion fails, log a warning and skip this entry
        if device_id is None:
            _LOGGER.warning(
                "Invalid device_id '%s' — expected a hex string (e.g. '0x27C8') "
                "or a decimal integer. Skipping entry.",
                raw_id,
            )
            continue

        # 取得型號與製造商，未填則使用預設值
        # Retrieve model and manufacturer, falling back to defaults if absent
        model = entry.get(CONF_MODEL, DEFAULT_MODEL)
        manufacturer = entry.get(CONF_MANUFACTURER, DEFAULT_MANUFACTURER)

        # broadlink.SUPPORTED_TYPES 的 value 格式為 (型號, 製造商)
        # The value format expected by broadlink.SUPPORTED_TYPES is (model, manufacturer)
        device_info = (model, manufacturer)

        if device_id not in broadlink.SUPPORTED_TYPES:
            # 尚未登錄，進行注入
            # Not yet registered — inject now
            broadlink.SUPPORTED_TYPES[device_id] = device_info
            _LOGGER.info(
                "Registered Broadlink device: id=%s, model='%s', manufacturer='%s'.",
                hex(device_id),
                model,
                manufacturer,
            )
            injected += 1
        else:
            # 已存在，跳過以避免覆蓋原有設定
            # Already registered — skip to avoid overwriting existing entry
            _LOGGER.debug(
                "Broadlink device id=%s is already registered. Skipping.",
                hex(device_id),
            )
            skipped += 1

    # ── 步驟 4：輸出摘要並回傳成功 / Step 4: Log summary and return success ───────
    _LOGGER.info(
        "Broadlink Device Patch complete: %d device(s) registered, %d already existed.",
        injected,
        skipped,
    )
    return True


async def async_setup(hass, config):
    """YAML 驅動的啟動路徑（進階使用者）。
    YAML-based setup path for power users who prefer configuration.yaml.

    此函式由 HA 在解析 configuration.yaml 後呼叫。
    Called by HA after parsing configuration.yaml.
    """
    # 取得本整合的設定區塊；若使用者未設定則使用空字典
    # Retrieve this integration's config block; use empty dict if absent
    domain_config = config.get(DOMAIN, {})

    # 取得裝置清單；若未設定則使用預設清單
    # Get the devices list; fall back to DEFAULT_DEVICES if not configured
    devices = domain_config.get(CONF_DEVICES, DEFAULT_DEVICES)

    return await _do_patch(devices)


async def async_setup_entry(hass, entry):
    """Config Entry 啟動路徑（透過 UI 安裝後每次 HA 重啟自動呼叫）。
    Config Entry setup path — called automatically on every HA restart
    after the integration has been added via the UI.

    裝置清單儲存於 Config Entry 的 options 中；
    若尚未設定任何裝置，則使用預設清單。
    Device list is stored in the Config Entry options;
    falls back to DEFAULT_DEVICES if no options have been saved yet.
    """
    # 從 Config Entry options 讀取裝置清單（若沒有就用預設值）
    # Read device list from Config Entry options (fall back to defaults if empty)
    devices = entry.options.get(CONF_DEVICES, DEFAULT_DEVICES)

    return await _do_patch(devices)


async def async_unload_entry(hass, entry):
    """移除 Config Entry 時呼叫。
    Called when the Config Entry is removed by the user.

    因為修補只在記憶體中進行，移除時不需要還原任何狀態。
    Since patching is purely in-memory, there is nothing to undo on unload.
    """
    return True
