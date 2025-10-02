# Timeline App

A Streamlit application to **upload program/module CSV files**, validate data, calculate durations, and display an interactive timeline with detailed module information. Includes support for **South African public holidays** when calculating working days.

---

## **Features**

* Upload a CSV file with programs and modules
* Validate required headers and data entries
* Ensure block/module dates fall within program dates
* Interactive timeline overview using **AgGrid**
* Clickable rows to view detailed module info

  * Shows all dates in module duration
  * Displays day of the week for each date
* Duration is displayed in the **most readable unit** (days, weeks, months)
* Workdays calculated considering **public holidays** (holidays on weekends shift to Monday)

---

## **CSV Template**

Required headers:

* Program Name
* Program Start Date
* Program End Date
* Dec Shutdown Start
* Dec Shutdown End
* Block/Module Name
* Block Start Date
* Block End Date

**Example row**:

| Program Name | Program Start Date | Program End Date | Dec Shutdown Start | Dec Shutdown End | Block/Module Name | Block Start Date | Block End Date |
| ------------ | ------------------ | ---------------- | ------------------ | ---------------- | ----------------- | ---------------- | -------------- |
| Data Science | 2025-01-05         | 2025-03-31       | 2025-12-01         | 2025-12-10       | Module 1          | 2025-01-05       | 2025-01-20     |

---

## **Installation**

1. Clone the repository:

```bash
git clone https://github.com/dowelani/timeline-app.git
cd timeline-app
```

2. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## **Technologies Used**

* Python
* Streamlit
* Pandas
* Streamlit-AgGrid (`st_aggrid`)
* Holidays (South Africa)

---

## **Author**

**Dowelani khumbelo shaun**

