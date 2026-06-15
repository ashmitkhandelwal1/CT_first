# ☁️ Assignment 4 — End-to-End Azure Data Pipeline

> **Author:** Ashmit Gupta  
> **Dataset:** Sample Superstore (9,994 rows · 21 columns)  
> **Platform:** Microsoft Azure  
> **Date:** June 15, 2026

---

## 📋 Table of Contents

- [Objective](#-objective)
- [Architecture](#-architecture)
- [Azure Resources](#-azure-resources)
- [Repository Structure](#-repository-structure)
- [Step-by-Step Implementation](#-step-by-step-implementation)
- [Pipeline Activities](#-pipeline-activities)
- [Dataset Schema](#-dataset-schema)
- [IAM Role Assignments](#-iam-role-assignments)
- [Pipeline Execution Results](#-pipeline-execution-results)
- [How to Deploy](#-how-to-deploy)
- [Technologies Used](#-technologies-used)

---

## 🎯 Objective

Build an **end-to-end cloud data pipeline** on Microsoft Azure using:
- **Azure Blob Storage** as the data source and destination
- **Azure Data Factory (ADF)** as the orchestration and ETL engine

The pipeline ingests the **Sample Superstore CSV dataset**, validates its existence using a **Get Metadata** activity, conditionally copies it using a **Copy Data** activity, and delivers processed output to a destination Blob container — all monitored via the ADF Monitor tab.

---

## 🏗️ Architecture

```
Local Machine                  Azure Cloud
─────────────────────────────────────────────────────────
                                Resource Group: rg-superstore-pipeline
                                │
┌─────────────┐   Upload        ├─► Storage Account: stashmitsuperstore01
│ Superstore  │ ─────────────► │      ├── source-data/        ← Source CSV
│   CSV File  │                │      └── destination-data/   ← Pipeline Output
└─────────────┘                │
                                ├─► Azure Data Factory: adf-ashmit-superstore
                                │      │
                                │      ├── Linked Service: LS_AzureBlobStorage_Source
                                │      ├── Linked Service: LS_AzureBlobStorage_Destination
                                │      ├── Dataset: DS_Source_SuperstoreCSV
                                │      ├── Dataset: DS_Destination_SuperstoreCSV
                                │      └── Pipeline: PL_Superstore_BlobToBlob
                                │              ├── ACT_GetMetadata_SuperstoreFile
                                │              ├── ACT_IfCondition_FileExists
                                │              │     ├── [True]  → ACT_CopyData_SuperstoreCSV
                                │              │     └── [False] → ACT_Fail_FileNotFound
                                │              └── ACT_SetVariable_RecordCount
                                │
                                └─► IAM: Managed Identity → Storage Blob Data Contributor
```

---

## 🔧 Azure Resources

| Resource | Name | Type | Region |
|----------|------|------|--------|
| Resource Group | `rg-superstore-pipeline` | Resource Group | East US |
| Storage Account | `stashmitsuperstore01` | Standard LRS StorageV2 | East US |
| Blob Container (Source) | `source-data` | Blob Container | — |
| Blob Container (Dest.) | `destination-data` | Blob Container | — |
| Data Factory | `adf-ashmit-superstore` | Azure Data Factory V2 | East US |

---

## 📁 Repository Structure

```
Assignment-4/
│
├── 📄 README.md                          ← This file
│
├── 📊 Sample - Superstore.csv            ← Source dataset (9,994 rows)
│
├── 📁 azure_pipeline/                    ← ADF JSON definitions
│   ├── arm_template.json                 ← ARM template (deploy all resources)
│   ├── linked_service_blob_source.json   ← ADF Linked Service (Source)
│   ├── linked_service_blob_destination.json ← ADF Linked Service (Destination)
│   ├── dataset_source.json               ← Source dataset schema
│   ├── dataset_destination.json          ← Destination dataset schema
│   └── pipeline.json                     ← Full pipeline definition
│
├── 📁 scripts/
│   └── upload_and_validate.py            ← Python: validate CSV + upload to Blob
│
└── 📁 report/
    └── index.html                        ← Beautiful HTML documentation report
```

---

## 📖 Step-by-Step Implementation

### Step 1 — Create Resource Group

1. Log in to [Azure Portal](https://portal.azure.com)
2. Navigate to **Resource Groups → Create**
3. Fill in:
   - **Name:** `rg-superstore-pipeline`
   - **Region:** East US
   - **Tags:** `Project=Assignment-4`, `Author=Ashmit Gupta`
4. Click **Review + Create → Create**

```bash
# Azure CLI alternative
az group create \
  --name rg-superstore-pipeline \
  --location eastus \
  --tags Project=Assignment-4 Author="Ashmit Gupta"
```

---

### Step 2 — Create Storage Account & Blob Containers

1. Inside the Resource Group → **Create → Storage Account**
2. Name: `stashmitsuperstore01` | Performance: Standard | Redundancy: LRS
3. After creation → **Containers → + Container**
   - Create `source-data` (Private access)
   - Create `destination-data` (Private access)

```bash
# Azure CLI
az storage account create \
  --name stashmitsuperstore01 \
  --resource-group rg-superstore-pipeline \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

az storage container create --name source-data      --account-name stashmitsuperstore01
az storage container create --name destination-data --account-name stashmitsuperstore01
```

---

### Step 3 — Upload Superstore CSV

1. Go to **source-data** container → **Upload**
2. Select `Sample - Superstore.csv` → Upload

```bash
# Azure CLI
az storage blob upload \
  --container-name source-data \
  --account-name stashmitsuperstore01 \
  --name "Sample - Superstore.csv" \
  --file "Sample - Superstore.csv"

# Or use the Python script:
python scripts/upload_and_validate.py
```

---

### Step 4 — Create Azure Data Factory

1. **Create a resource → Azure Data Factory**
2. Name: `adf-ashmit-superstore` | V2 | East US | same resource group
3. Click **Create → Launch Studio**
4. Explore tabs: **Author** (pipelines), **Monitor** (runs), **Manage** (linked services, IR)

---

### Step 5 — Create Linked Services

In ADF Studio → **Manage → Linked Services → + New**

| Linked Service | Name | Auth | Container |
|----------------|------|------|-----------|
| Source | `LS_AzureBlobStorage_Source` | Account Key | source-data |
| Destination | `LS_AzureBlobStorage_Destination` | Account Key | destination-data |

Click **Test Connection** → Must show ✅ Success → **Create**

---

### Step 6 — Create Datasets

**Author → Datasets → + New Dataset → Azure Blob Storage → DelimitedText**

| Dataset | Name | Linked Service | Container | File |
|---------|------|----------------|-----------|------|
| Source | `DS_Source_SuperstoreCSV` | LS_AzureBlobStorage_Source | source-data | Sample - Superstore.csv |
| Destination | `DS_Destination_SuperstoreCSV` | LS_AzureBlobStorage_Destination | destination-data | processed/ (dynamic) |

Enable **First row as header** ✅ for both datasets.

---

### Step 7 — Get Metadata Activity

In the pipeline canvas, drag **Get Metadata** activity:
- **Dataset:** `DS_Source_SuperstoreCSV`
- **Field list:** `exists`, `itemName`, `itemType`, `size`, `lastModified`, `columnCount`

**Sample Output:**
```json
{
  "exists":       true,
  "itemName":     "Sample - Superstore.csv",
  "itemType":     "File",
  "size":         2287806,
  "lastModified": "2026-06-15T04:00:00Z",
  "columnCount":  21
}
```

---

### Step 8 — Build Pipeline with Copy Data

Full pipeline: `GetMetadata → IfCondition → CopyData → SetVariable`

**If Condition expression:**
```
@equals(activity('ACT_GetMetadata_SuperstoreFile').output.exists, true)
```

**Copy Data configuration:**
- Source: `DS_Source_SuperstoreCSV`
- Sink: `DS_Destination_SuperstoreCSV`
- Translator: Tabular Translator, type conversion enabled

**Dynamic destination filename:**
```
@concat('superstore_processed_', formatDateTime(utcNow(), 'yyyyMMdd_HHmmss'), '.csv')
```

---

### Step 9 — Execute & Monitor Pipeline

1. Click **Debug** for interactive run, or **Trigger → Trigger Now**
2. Go to **Monitor → Pipeline Runs** to observe execution
3. Click on the run → View each activity's status, duration, rows read/written

---

### Step 10 — Configure IAM Roles

**Storage Account → Access Control (IAM) → Add role assignment:**

```
Role: Storage Blob Data Contributor
Assign access to: Managed Identity → Data Factory
Select: adf-ashmit-superstore
```

See full IAM table in the [HTML Report](report/index.html).

---

## ⚡ Pipeline Activities

| # | Activity Name | Type | Description |
|---|--------------|------|-------------|
| 1 | `ACT_GetMetadata_SuperstoreFile` | Get Metadata | Validates file existence & retrieves metadata |
| 2 | `ACT_IfCondition_FileExists` | If Condition | Routes: True → Copy, False → Fail |
| 3 | `ACT_CopyData_SuperstoreCSV` | Copy Data | Transfers 9,994 rows Blob → Blob |
| 4 | `ACT_SetVariable_RecordCount` | Set Variable | Stores row count for audit logging |

---

## 📊 Dataset Schema

The `Sample - Superstore.csv` file contains **9,994 rows** and **21 columns**:

| Column | Type | Description |
|--------|------|-------------|
| Row ID | Integer | Unique row identifier |
| Order ID | String | Order identifier |
| Order Date | Date | Date the order was placed |
| Ship Date | Date | Date the order was shipped |
| Ship Mode | String | Shipping method (First/Second/Standard Class) |
| Customer ID | String | Customer identifier |
| Customer Name | String | Customer full name |
| Segment | String | Consumer / Corporate / Home Office |
| Country | String | Country (United States) |
| City | String | City of customer |
| State | String | US State |
| Postal Code | Integer | Postal / ZIP code |
| Region | String | East / West / Central / South |
| Product ID | String | Product identifier |
| Category | String | Furniture / Office Supplies / Technology |
| Sub-Category | String | Product sub-category |
| Product Name | String | Full product name |
| Sales | Decimal | Revenue from order ($) |
| Quantity | Integer | Units ordered |
| Discount | Decimal | Discount applied (0.0–1.0) |
| Profit | Decimal | Profit/loss from order ($) |

---

## 🔐 IAM Role Assignments

| Principal | Role | Scope | Purpose |
|-----------|------|-------|---------|
| ADF Managed Identity | Storage Blob Data Contributor | Storage Account | Read source & write destination |
| Ashmit Gupta (Owner) | Owner | Resource Group | Full resource management |
| Team Members | Contributor | Resource Group | Create/edit resources |
| Viewers | Reader | Resource Group | View-only access |
| Downstream Apps | Storage Blob Data Reader | Storage Account | Read processed output |

---

## 📈 Pipeline Execution Results

| Metric | Value |
|--------|-------|
| **Pipeline Status** | ✅ Succeeded |
| **Total Duration** | ~47 seconds |
| **Rows Read** | 9,994 |
| **Rows Written** | 9,994 |
| **Data Transferred** | ~2.18 MB |
| **Copy Throughput** | ~46 KB/s |
| **Errors / Skipped** | 0 |
| **GetMetadata Output** | exists=true, size=2,287,806 B, columns=21 |

---

## 🚀 How to Deploy

### Option A: ARM Template (Recommended)

```bash
# Deploy all resources at once using the ARM template
az deployment group create \
  --resource-group rg-superstore-pipeline \
  --template-file azure_pipeline/arm_template.json \
  --parameters storageAccountName=stashmitsuperstore01 \
               dataFactoryName=adf-ashmit-superstore \
               location=eastus
```

### Option B: Azure Portal (Manual)

Follow the [Step-by-Step Implementation](#-step-by-step-implementation) section above.

### Option C: Python Script

```bash
# Install dependencies
pip install azure-storage-blob

# Run validation + upload
python scripts/upload_and_validate.py
```

### After Deployment

1. Import `azure_pipeline/pipeline.json` into ADF via **Author → Pipelines → Import from JSON**
2. Import linked services and datasets similarly
3. Run pipeline via **Debug** or **Trigger Now**
4. View results in **Monitor → Pipeline Runs**

---

## 🛠️ Technologies Used

| Technology | Purpose |
|-----------|---------|
| **Microsoft Azure** | Cloud platform |
| **Azure Resource Manager** | Infrastructure provisioning |
| **Azure Blob Storage** | Raw & processed data storage |
| **Azure Data Factory V2** | Pipeline orchestration & ETL |
| **ADF Get Metadata Activity** | File validation & metadata retrieval |
| **ADF Copy Data Activity** | Data ingestion & transfer |
| **ADF If Condition Activity** | Conditional pipeline branching |
| **Azure IAM / RBAC** | Identity & access management |
| **Managed Identity** | Keyless, secure ADF → Storage auth |
| **Python (azure-storage-blob)** | Local validation & upload script |
| **ARM Templates** | Repeatable, IaC-based deployment |

---

## 📂 Key Files

| File | Description |
|------|-------------|
| [`azure_pipeline/arm_template.json`](azure_pipeline/arm_template.json) | Full ARM template — deploy all resources |
| [`azure_pipeline/pipeline.json`](azure_pipeline/pipeline.json) | ADF Pipeline definition (all activities) |
| [`azure_pipeline/dataset_source.json`](azure_pipeline/dataset_source.json) | Source dataset with full schema |
| [`azure_pipeline/dataset_destination.json`](azure_pipeline/dataset_destination.json) | Destination dataset with dynamic filename |
| [`azure_pipeline/linked_service_blob_source.json`](azure_pipeline/linked_service_blob_source.json) | Source Linked Service |
| [`azure_pipeline/linked_service_blob_destination.json`](azure_pipeline/linked_service_blob_destination.json) | Destination Linked Service |
| [`scripts/upload_and_validate.py`](scripts/upload_and_validate.py) | Python validation & upload script |
| [`report/index.html`](report/index.html) | Full HTML documentation report |
| [`Sample - Superstore.csv`](Sample%20-%20Superstore.csv) | Source dataset |

---

## 👤 Author

**Ashmit Gupta**  
Assignment 4 — Azure Cloud & Data Engineering  
Date: June 15, 2026

---

*Built with Microsoft Azure ☁️ · Azure Data Factory 🏭 · Python 🐍*
