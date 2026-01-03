# Industrial Data Pipeline & Tag Automation

Tooling for industrial automation, split into two core modules:

- **OT → IT monitoring** (OPC UA data collection and persistence to SQL Server)
- **Engineering automation** (bulk tag creation in KepServerEX via REST)

Designed to be **scalable**, **maintainable**, and suitable for **24/7 shop-floor operation**.

---

## 📁 Repository Layout

### `monitor_service/` — Data Collection Service (24/7)

Mission-critical service intended to run continuously on the plant network.

**What it does**
- Reads process data via **OPC UA**
- Persists it into **SQL Server**

**Key features**
- Data-loss protection via a **local CSV buffer**
- **Automatic cache cleanup**
- Ready to run as a **Windows Service**

**Ports**
- OPC UA: `49320` (default)
- SQL Server: `1433` / `1600`

---

### `tag_automation/` — Tag Engineering Automation

Productivity tooling for SCADA/OPC configuration.

**What it does**
- Creates tags in **KepServerEX** in bulk via **REST API**

**Key features**
- Converts **CSV/Excel tag lists** into tag configuration payloads
- Saves hours of manual setup

**Ports**
- KepServer REST/HTTP: `57412` (default)

---

### `utils/`

Helper scripts and test utilities.

---

## 🚀 Quick Start

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Monitoring Service

1. Configure variables in:
   - `monitor_service/cam_monitor_service.py` **or**
   - `config.ini`

2. Install it as a Windows Service using the scripts under:
   - `monitor_service/`

---

## 🏷️ Create Tags (KepServerEX)

1. Update your tag list:
   - `tag_automation/taglist.csv`

2. Run:

```bash
python tag_automation/create_tag2.py
```

---

## Notes

- Default ports are documented above; adjust them if your environment uses different mappings.
- This repository keeps the **runtime collector** (monitoring) separated from **engineering utilities** (tag automation), which helps long-term maintenance.

---

*Built for scalability and long-term maintainability.*
