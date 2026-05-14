# Broadlink Device Patch

> English documentation below ↓

---

## 為什麼做這個

我有一台 Broadlink RM mini 3，但 Home Assistant 一直認不出來。後來查了才知道是因為這台裝置的型別 ID（`0x27C8`）根本不在官方的支援清單裡，所以 HA 不知道該怎麼處理它。

當時的解法是手動去改 `python-broadlink` 函式庫裡面的檔案——改完確實可以用，但只要函式庫一更新，改動就不見了，又要重來一遍。改了幾次之後覺得實在很煩。

所以就寫了這個小整合，讓它在每次 HA 啟動時自動把裝置資訊補進去。從此不用再手動改任何檔案，更新也不怕。

---

## 安裝方式

1. 把 `broadlink_patch` 資料夾放到 `custom_components` 目錄裡：

   ```
   config/
   └── custom_components/
       └── broadlink_patch/
           ├── __init__.py
           ├── manifest.json
           ├── strings.json
           └── translations/
               ├── en.json
               └── zh-TW.json
   ```

2. 在 `configuration.yaml` 加上這段：

   ```yaml
   broadlink_patch:
     devices:
       - device_id: "0x27C8"
         model: "RM mini 3"
         manufacturer: "Broadlink"
   ```

3. 重啟 Home Assistant，搞定。

---

## 設定說明

| 鍵名 | 必填 | 預設值 | 說明 |
|---|---|---|---|
| `devices` | 否 | RM mini 3 (`0x27C8`) | 要補進去的裝置清單 |
| `devices[].device_id` | **是** | — | 裝置的十六進位型別 ID，例如 `"0x27C8"` |
| `devices[].model` | 否 | `"Unknown"` | 型號名稱，自己取就好 |
| `devices[].manufacturer` | 否 | `"Broadlink"` | 製造商名稱 |

可以同時新增多台裝置：

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

### 怎麼知道自己的裝置 ID 是多少？

HA 認不出裝置的時候，日誌裡通常會出現這樣的訊息：

```
Unsupported Broadlink device: type 0x27C8
```

那個十六進位數字就是你需要的 `device_id`。

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

1. Drop the `broadlink_patch` folder into your `custom_components` directory:

   ```
   config/
   └── custom_components/
       └── broadlink_patch/
           ├── __init__.py
           ├── manifest.json
           ├── strings.json
           └── translations/
               ├── en.json
               └── zh-TW.json
   ```

2. Add this to your `configuration.yaml`:

   ```yaml
   broadlink_patch:
     devices:
       - device_id: "0x27C8"
         model: "RM mini 3"
         manufacturer: "Broadlink"
   ```

3. Restart Home Assistant. Done.

---

## Configuration

| Key | Required | Default | Description |
|---|---|---|---|
| `devices` | No | RM mini 3 (`0x27C8`) | List of devices to patch in |
| `devices[].device_id` | **Yes** | — | The hex type ID of your device, e.g. `"0x27C8"` |
| `devices[].model` | No | `"Unknown"` | Whatever you want to call it |
| `devices[].manufacturer` | No | `"Broadlink"` | Manufacturer name |

You can add as many devices as you need:

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

## Languages

| Language | File |
|---|---|
| English | `translations/en.json` |
| 繁體中文 | `translations/zh-TW.json` |

PRs for other languages are welcome!

---

## License

MIT
