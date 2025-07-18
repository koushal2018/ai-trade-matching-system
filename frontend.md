# 📘 Front-End Design Document: Trade Reconciliation System

## 🧭 Overview

This front-end UI is designed to enable reconciliation analysts, operations teams, and auditors to:
- Upload trade documents (PDFs)
- Monitor trade reconciliation status
- Review matched and unmatched trades
- View field-level discrepancies
- Download or browse detailed reconciliation reports

---

## 🧱 Pages Overview

| Page | Purpose |
|------|---------|
| **1. Dashboard** | Overview of reconciliation health |
| **2. Document Upload** | Upload PDFs for trade ingestion |
| **3. Trade Explorer** | Browse/search trades |
| **4. Match Review** | Inspect suggested trade pairings |
| **5. Reconciliation Detail** | Field-level comparison |
| **6. Reports** | Browse/download reconciliation reports |
| **7. Admin Settings** *(optional)* | Manage thresholds, tolerances |

---

## 1️⃣ Dashboard

**Purpose:** Executive summary of reconciliation progress.

### Components:
- **Summary Cards**:
  - ✅ Matched Trades: 120
  - ⚠️ Partially Matched: 18
  - ❌ Unmatched Trades: 7
- **Charts**:
  - 📈 Trades Processed Over Time (Line chart)
  - 🎯 Status Distribution (Donut/Pie chart)
- **Quick Links**:
  - ➕ Upload Trade PDFs
  - 📄 View Reports
  - 🔍 Trade Explorer

---

## 2️⃣ Document Upload

**Purpose:** Upload new trade documents for ingestion.

### Components:
- **File Upload Box** (Drag & Drop + Browse):
  - Accepts: `.pdf`
  - Multiple uploads allowed
- **Metadata Form** (optional):
  - Source: `Bank` / `Counterparty`
  - Trade Date Range (optional)
- **Upload Progress Indicator**
- **Success/Error Status Messages**

---

## 3️⃣ Trade Explorer

**Purpose:** Search, filter, and review all trades.

### Components:
- **Filter Panel**:
  - Source: `Bank` / `Counterparty`
  - Matched Status
  - Currency
  - Trade Date Range
- **Search Box**:
  - By `Trade ID` or `Internal Reference`
- **Data Table**:

  | Trade ID | Source | Notional | Currency | Trade Date | Matched Status | Match Score |

- **Actions**:
  - 🔍 View Trade
  - 🔗 View Match Details

---

## 4️⃣ Match Review

**Purpose:** Review suggested trade matches.

### Components:
- **Data Table**:

  | Bank Trade ID | Counterparty Trade ID | Match Score | Status | Action |

- **Status Tags**: `Pending`, `Matched`, `Unmatched`
- **Action Buttons**:
  - 👁 View Reconciliation
  - ✅ Confirm Match
  - ❌ Reject Match
- **Sort/Filter**: By score or date

---

## 5️⃣ Reconciliation Detail

**Purpose:** Inspect field-level comparison for matched trades.

### Components:
- **Trade Pair Summary**:
  - Bank Trade ID / Counterparty Trade ID
  - Match Score: `92%`
- **Field Comparison Table**:

  | Field       | Bank Value   | Cpty Value   | Status      | Reason                     |
  |-------------|--------------|--------------|-------------|----------------------------|
  | Notional    | 10,000,000   | 9,995,000    | ⚠️ MISMATCHED | Difference > 0.5%         |
  | Currency    | USD          | USD          | ✅ MATCHED  |                            |
  | Maturity    | 2026-03-15   | 2026-03-15   | ✅ MATCHED  |                            |

- **Overall Reconciliation Status**:
  - `Partially Matched`, `Fully Matched`, `Critical Mismatch`

---

## 6️⃣ Reports

**Purpose:** View/download reconciliation summaries.

### Components:
- **Filter Panel**:
  - Date Range
  - Reconciliation Status
- **Report List Table**:

  | Report ID | Generated On | Match Summary | Status | Download |

- **Actions**:
  - 📥 Download (JSON or PDF)
  - 👁 View Report

---

## 7️⃣ Admin Settings *(Optional)*

**Purpose:** Configure system tolerances and thresholds.

### Components:
- **Threshold Configs**:
  - Match Score Threshold: `90%`
  - Notional Tolerance: `1%`
- **Field Criticality Settings**
- **Save & Reset Buttons**
- **Access Control Panel**

---

## 🧑‍💻 Tech Recommendations

- **Framework:** React.js + Tailwind CSS
- **State Management:** Zustand / Redux
- **API Integration:** Axios (backend REST endpoints or GraphQL)
- **Auth:** AWS Cognito or IAM Identity Center
- **PDF Upload:** Direct to S3 via signed URL
- **Data Source:** DynamoDB + S3 for reports

---

## 🏁 User Workflow

1. **User uploads trade PDF**
2. **System extracts data and stores in DynamoDB**
3. **Dashboard updates with new status**
4. **Analyst views matched/unmatched pairs**
5. **Drills into field-level comparison**
6. **Downloads reports or exports for audit**
