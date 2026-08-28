# FAERS pharmacovigilanc analysis with VigiMatch depublication - Installation Guide

Follow these instructions to install and run the FAERS Disproportionality Analysis pipeline from GitHub:

## Requirements

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

---

## Step-by-Step Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd FAERS_PHARMACOVIGILANCE_ANALYSIS
```

### 2. Set Up a Virtual Environment (optional but recommended)

```bash
python -m venv venv
venv\Scripts\activate          # On Windows
# source venv/bin/activate    # On Linux/macOS
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> If you're using Jupyter Notebook, you can also run:
```bash
pip install notebook
```

### 4. Download and Place FAERS Data

Download quarterly **DRUG** and **REAC** `.TXT` files from the [FDA FAERS portal](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html).

Unzip and move the TXT files into a folder called:

```bash
data-source/
```

Structure should look like:

```
FAERS_PHARMACOVIGILANCE_ANALYSIS/
├── data-source/
│   ├── DRUG25Q1.txt
│   ├── REAC25Q1.txt
│   └── ...
```

### 5. Run the Analysis Notebook

```bash
jupyter notebook
```

Then open `FAERS_Pharmacovigilance_Analysis.ipynb` (or `FAERS_Pharmacovigilance_Analysis_with_Bayesian_methods.ipynb`) and follow the cells to:

- Configure drug/event names
- Load and preprocess FAERS data
- Run ROR/PRR analysis
- Export results to Excel

---

## Output

Results are saved as an Excel file (you can change the name of the excel file):

```
FAERS_xxx_Results.xlsx   # adjust name according to preference
```

---

## Citations & Attribution

If used in academic work, please cite this repository and include a link to the GitHub page. The methodology includes VigiMatch-style deduplication and supports pharmacovigilance reproducibility.
