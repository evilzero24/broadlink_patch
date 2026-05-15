# Broadlink Device Patch

> English documentation below ↓

---

## 為什麼做這個

我有一台 Broadlink RM mini 3，但 Home Assistant 一直認不出來。後來查了才知道是因為這台裝置的型別 ID（`0x27C8`）根本不在官方的支援清單裡，所以 HA 不知道該怎麼處理它。

當時的解法是手動去改 `python-broadlink` 函式庫裡面的檔案——改完確實可以用，但只要函式庫一更新，改動就不見了，又要重來一遍。改了幾次之後覺得實在很煩。

所以就寫了這個小整合，讓它在每次 HA 啟動時自動把裝置資訊補進去。從此不用再手動改任何檔案，更新也不怕。

---

## 安裝方式

### 方法一：透過 HACS（推薦）

1. 在 HACS 搜尋 **Broadlink Device Patch** 並安裝
2. 重啟 Home Assistant
3. 前往 **Settings → Devices & Services → Add Integration**
4. 搜尋 **Broadlink Device Patch**，按送出
5. 再重啟一次，預設裝置（RM mini 3, `0x27C8`）就會自動注入

### 方法二：手動複製

把 `broadlink_patch` 資料夾放到 `custom_components` 目錄裡：

```
config/
└── custom_components/
    └── broadlink_patch/
        ├── __init__.py
        ├── config_flow.py
        ├── manifest.json
        ├── strings.json
        └── translations/
            ├── en.json
            └── zh-TW.json
```

接著同樣到 **Settings → Devices & Services → Add Integration** 加入整合。

---

## 管理裝置

安裝完成後，點整合卡片上的**設定**按鈕，就能看到目前已有的裝置清單，並選擇：

- **新增裝置**：填入裝置 ID、型號、製造商，送出後儲存
- **移除裝置**：勾選想刪除的裝置，送出後移除（不會影響整合本身）

整合卡片的標題也會同步顯示目前有哪些裝置，一眼就看清楚。

如果偏好 YAML，也可以在 `configuration.yaml` 裡設定，重啟後會一併套用：

```yaml
broadlink_patch:
  devices:
    - device_id: "0x27C8"
      model: "RM mini 3"
      manufacturer: "Broadlink"
    - device_id: "0x5F36"
      model: "RM4 mini"
      manufacturer: "Broadlink"
    - device_id: "0x648B"
      model: "RM4 Pro"
      manufacturer: "Broadlink"
```

| 鍵名 | 必填 | 預設值 | 說明 |
|---|---|---|---|
| `device_id` | **是** | — | 裝置的十六進位型別 ID，例如 `"0x27C8"` |
| `model` | 否 | `"Unknown"` | 型號名稱，自己取就好 |
| `manufacturer` | 否 | `"Broadlink"` | 製造商名稱 |

### 怎麼知道自己的裝置 ID？

HA 認不出裝置的時候，日誌裡通常會出現這樣的訊息：

```
Unsupported Broadlink device: type 0x27C8
```

那個十六進位數字就是你需要的 `device_id`。

---

## 常見問題

**整合頁面搜尋不到 Broadlink Patch？**

1. HACS 安裝完成後，必須先**重啟 HA** 才能讓 HA 認識新的 custom component
2. 重啟後再到 Settings → Devices & Services → Add Integration 搜尋
3. 如果還是找不到，到 HA 的 **Settings → System → Logs** 搜尋 `broadlink_patch`，看有沒有載入錯誤

**裝置注入了但 HA 還是認不出裝置？**

- 確認裝置 ID 是對的（從日誌裡的 `Unsupported Broadlink device: type 0x????` 取得）
- 確認整合已啟用，且重啟過 HA

---

## 支援語言

| 語言 | 檔案 |
|---|---|
| English | `translations/en.json` |
| 繁體中文 | `translations/zh-TW.json` |

歡迎提 PR 新增其他語言！

---

---

## Why I made this

I have a Broadlink RM mini 3 that Home Assistant just wouldn't pick up. Turns out the device type ID (`0x27C8`) wasn't in the official support list, so HA had no idea what to do with it.

The "fix" was to manually edit a file inside the `python-broadlink` library — which worked fine until the library updated and wiped my change. Had to do it all over again. Pretty annoying.

So I wrote this small integration that does the patching automatically every time HA starts. No more editing library files by hand, no more losing the fix after an update.

---

## How to install

### Option 1: HACS (recommended)

1. Search for **Broadlink Device Patch** in HACS and install it
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration**
4. Search for **Broadlink Device Patch** and click Submit
5. Restart once more — the default device (RM mini 3, `0x27C8`) will be patched in automatically

### Option 2: Manual

Copy the `broadlink_patch` folder into your `custom_components` directory:

```
config/
└── custom_components/
    └── broadlink_patch/
        ├── __init__.py
        ├── config_flow.py
        ├── manifest.json
        ├── strings.json
        └── translations/
            ├── en.json
            └── zh-TW.json
```

Then add the integration the same way via **Settings → Devices & Services → Add Integration**.

---

## Managing devices

After setup, click the **Configure** button on the integration card. You'll see a list of currently registered devices and can choose:

- **Add device**: Enter the device ID, model, and manufacturer, then submit
- **Remove device**: Check the devices you want to delete and submit — the integration itself stays intact

The integration card title will also update to show which devices are currently registered.

If you prefer YAML, you can also add devices in `configuration.yaml` — they'll be patched in on the next restart:

```yaml
broadlink_patch:
  devices:
    - device_id: "0x27C8"
      model: "RM mini 3"
      manufacturer: "Broadlink"
    - device_id: "0x5F36"
      model: "RM4 mini"
      manufacturer: "Broadlink"
    - device_id: "0x648B"
      model: "RM4 Pro"
      manufacturer: "Broadlink"
```

| Key | Required | Default | Description |
|---|---|---|---|
| `device_id` | **Yes** | — | The hex type ID of your device, e.g. `"0x27C8"` |
| `model` | No | `"Unknown"` | Whatever you want to call it |
| `manufacturer` | No | `"Broadlink"` | Manufacturer name |

### How do I find my device's type ID?

When HA can't recognise a Broadlink device, it usually logs something like this:

```
Unsupported Broadlink device: type 0x27C8
```

That hex number is your `device_id`.

---

## How it works (roughly)

When HA starts up, this integration grabs the `broadlink.SUPPORTED_TYPES` dictionary and adds your devices to it. Nothing on disk is touched — it's all in memory, so it just runs again on the next restart.

---

## Troubleshooting

**Can't find Broadlink Patch in the integrations search?**

1. After HACS installs the component, you **must restart HA** before it's recognised
2. Then go to Settings → Devices & Services → Add Integration and search for it
3. If it still doesn't appear, check **Settings → System → Logs** and search for `broadlink_patch` to see if there's a loading error

**Device was injected but HA still can't find the device?**

- Double-check the device ID (grab it from the log line `Unsupported Broadlink device: type 0x????`)
- Make sure the integration is enabled and HA has been restarted

---

## Languages

| Language | File |
|---|---|
| English | `translations/en.json` |
| 繁體中文 | `translations/zh-TW.json` |

PRs for other languages are welcome!

---

## License

MIT

