# FAERS & EudraVigilance Pharmacovigilance Analysis: Step-by-Step Complete Guide

---

## High-Level Roadmap: Humne Is Project Me Kya-Kya Analysis Kiya?

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Data Ingestion (Raw FAERS ASCII & EudraVigilance Download)                │
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 2: Encoding Resilience & File Cleaning (UTF-8 / Latin-1 Fallback)          │
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 3: Primary Suspect Filtering (role_cod == 'PS')                            │
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 4: VigiMatch-Style Deduplication (FAERS Vector Keys & SHA-256 Hashing)    │
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 5: Medical Ontology & Synonym Mapping (Brand->Generic & MedDRA Explosion)   │
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 6: 2x2 Contingency Matrix Building (Counting A, B, C, D)                    │
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 7: Frequentist Screening Engine (ROR, PRR, Haldane OR, Fisher's, Chi2 Yates)│
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 8: Bayesian Validation Engine (WHO BCPNN IC & 50,000 Beta Monte Carlo Sims)  │
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 9: Real Case Study Results (Capivasertib & Stomatitis Signals)               │
├──────────────────────────────────────────────────────────────────────────────────┤
│ STEP 10: Executive Output & Business Recommendations (Label Updates & Risk Plans)│
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## STEP 1: Data Ingestion & File Loading

### 1. Humne Kya Kiya? (What did we do in code?)
Humne Python script me `load_files()` function banaya jo selected Year/Quarter range (jaise Q4 2023 se Q1 2025) ke raw FDA FAERS dollar-separated (`$`) text files (`DRUG.txt` aur `REAC.txt`) aur EudraVigilance Excel files ko automatic folder me search karke memory me load karta hai.

### 2. Wo Hota Kya Hai? (What is it in simple terms?)
Ye humara **Data Ingestion / Extraction Phase** hai. FDA har teen mahine (quarterly) me poore USA ki drug safety reports ka zip folder release karta hai. Usme alag-alag text files hoti hain. Humne code likha jo bina manual file khole direct python me saare quarters combine kar leta hai.

### 3. Isse Kya Hua / Benefit Kya Mila? (What did it achieve?)
- **11.6 Million Drug Records** aur **8.7 Million Reaction Records** ek baar me Python memory me load ho gaye.
- Dynamic date range filter lagaya jisse analyst ko hardcode nahi karna padta—bas `(2023, 4)` aur `(2025, 1)` dene par target files auto-load ho jaati hain.

### 4. Interview me Kaise Bolna Hai?
> *"Step 1 was Data Ingestion. I wrote a dynamic loader function in Python that uses regex pattern matching to pull multi-quarter raw ASCII text archives from FDA FAERS and EudraVigilance directly into Pandas DataFrames."*

---

## STEP 2: Text Encoding & Data Parsing Resilience

### 1. Humne Kya Kiya? (What did we do in code?)
Files read karte waqt try/except block lagaya:
```python
try:
    df = pd.read_csv(file, sep='$', encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(file, sep='$', encoding='latin1')
```
Jo lines corrupt thi ya format bigda hua tha unhe crash hone ke bajaye skip karke `skipped_rows_log` CSV file me save kar diya.

### 2. Wo Hota Kya Hai? (What is it in simple terms?)
Ye **Data Quality / Encoding Cleaning** hai. Global text files me alag-alag country ke characters hotey hain. Kuch files modern `UTF-8` me hoti hain, kuch purani `Latin-1` me. Agar Python galat encoding se padhega to code crash ho jaata hai.

### 3. Isse Kya Hua / Benefit Kya Mila? (What did it achieve?)
- Code 10+ Million rows padhte waqt **kabhi crash nahi hua**.
- Saara audit log transparent raha—hum dikha sakte hain ki kitni corrupt lines skip hui (`csv_log_output.csv`).

### 4. Interview me Kaise Bolna Hai?
> *"Step 2 was Encoding Cleaning. Because FAERS collects data globally, text encodings vary. I built a multi-encoding fallback mechanism trying UTF-8 first and falling back to Latin-1, while logging any corrupt rows into an audit log to ensure pipeline stability."*

---

## STEP 3: Primary Suspect Filtering (`role_cod == 'PS'`)

### 1. Humne Kya Kiya? (What did we do in code?)
`DRUG.txt` table me column `role_cod` ko filter karke sirf `'PS'` (Primary Suspect) rows ko rakha, baaki `SS` (Secondary), `C` (Concomitant), aur `I` (Interacting) drugs ko hataya:
```python
df_drug_ps = df_drug[df_drug['role_cod'].str.upper() == 'PS']
```

### 2. Wo Hota Kya Hai? (What is it in simple terms?)
Ek patient agar cancer ki dava (Primary Suspect) le raha hai, to saath me multivitamin, blood pressure ki goli, acidity ki goli bhi le raha hota hai (Concomitant drugs). Concomitant drugs ka side effect se koi lene-dena nahi hota. Primary Suspect Filter ka matlab hai **sirf us dava ko pakadna jispar doctor ko shak hai**.

### 3. Isse Kya Hua / Benefit Kya Mila? (What did it achieve?)
- **False Noise Khatam Ho Gaya:** Agar hum multivitamin ko bhi include kar lete, to oncology drug ka side effect multivitamin ke naam par chadh jaata.
- Data size chhota ho gaya jisse overall process speed 5x fast ho gayi.

### 4. Interview me Kaise Bolna Hai?
> *"Step 3 was Primary Suspect Filtering. Patients often take multiple background medications like vitamins alongside their main treatment. I filtered strictly for role_cod == 'PS' to isolate the primary suspected drug and prevent concomitant drugs from polluting causal attribution."*

---

## STEP 4: Deduplication (WHO VigiMatch Methodology)

### 1. Humne Kya Kiya? (What did we do in code?)
- **FAERS Data:** Deduplicate kiya composite key par: `['primaryid', 'drugname_norm', 'route', 'dose_vbm']`.
- **EudraVigilance Data:** `primaryid` na hone par patient traits ka cryptographic SHA-256 hash banaya:
  $$\text{Hash Input} = \text{age} \parallel \text{sex} \parallel \text{drug\_name} \parallel \text{reaction\_term} \parallel \text{reporter\_country} \parallel \text{reported\_date}$$
  Aur duplicate hashes ko drop kar diya.

### 2. Wo Hota Kya Hai? (What is it in simple terms?)
Spontaneous reporting me duplicate reports aate hain. Ek hi patient ki bimari ki report doctor bhi bhejta hai, patient bhi bhejta hai, hospital bhi aur lawyer bhi. Agar ek hi case 5 baar count ho gaya, to dava bina vajah dangerous dikhne lagegi! Deduplication ka matlab hai **duplicate reports ko pehchan kar ek baar count karna**.

### 3. Isse Kya Hua / Benefit Kya Mila? (What did it achieve?)
- Per quarter **13,929 se 23,308 duplicate reports drop hue**.
- Co-occurrence count $A$ fake tarike se inflate hone se bach gaya (False Alarm prevention).

### 4. Interview me Kaise Bolna Hai?
> *"Step 4 was Deduplication using WHO VigiMatch guidelines. Spontaneous databases suffer from duplicate bias when doctors, patients, and hospitals report the same event. I constructed composite key vectors and SHA-256 demographic hashes, removing over 20,000 redundant records per quarter."*

---

## STEP 5: Medical Term Normalization & Synonym Explosion

### 1. Humne Kya Kiya? (What did we do in code?)
Regex list banakar alag-alag brand names ko active generic ingredient me convert kiya:
- `['OZEMPIC', 'WEGOVY', 'SEMAGLUTIDE']` $\rightarrow$ `SEMAGLUTIDE`
- MedDRA Preferred Terms ko group kiya: `['STOMATITIS', 'MOUTH ULCERATION', 'APHTHOUS ULCER', 'ORAL PAIN']`.

### 2. Wo Hota Kya Hai? (What is it in simple terms?)
Ye **Data Standardization** hai. Ek aadmi Ozempic likhta hai, doosra Wegovy, teesra Semaglutide. Computer ke liye ye 3 alag drugs hain. Synonym normalization se teeno ko ek hi bucket me daal diya jaata hai.

### 3. Isse Kya Hua / Benefit Kya Mila? (What did it achieve?)
- **Signal Dilution Prevent Hua:** Agar 100 cases Ozempic ke hain, 100 Wegovy ke, 100 Semaglutide ke, to bina normalization ke computer bolta "Teeno me sirf 100 cases hain, koi khatra nahi hai". Normalize karne par teeno milkar **300 cases** ban gaye aur STRONG SIGNAL detect ho gaya!

### 4. Interview me Kaise Bolna Hai?
> *"Step 5 was Medical Term Normalization. Different reporters use brand names or clinical synonyms. I mapped trade names like Ozempic and Wegovy to generic Semaglutide, and grouped MedDRA Preferred Terms. This resolved signal dilution, combining fragmented weak counts into a single statistically powerful signal."*

---

## STEP 6: 2x2 Contingency Matrix Building

### 1. Humne Kya Kiya? (What did we do in code?)
Target Drug aur Target Reaction ko poore FDA database ke background se compare karne ke liye 4 numbers calculate kiye:

```
                      Target Reaction (Yes)    Other Reactions (No)
Target Drug (Yes)               A                       B
Other Drugs (No)                C                       D
```

- **$A$:** Target Drug + Target Reaction (Dava + Reaction dono saath me hue)
- **$B$:** Target Drug + Other Reactions (Dava li, par reaction koi aur tha)
- **$C$:** Other Drugs + Target Reaction (Reaction hua, par kisi aur dava se)
- **$D$:** Other Drugs + Other Reactions (General Database background noise)

### 2. Wo Hota Kya Hai? (What is it in simple terms?)
Ye ek **Cross-Tabulation Table** hai. Iska maqsad ye check karna hai ki kya humari dava me is side effect ka ratio ($\frac{A}{B}$) baaki saari davao ke baseline ratio ($\frac{C}{D}$) se significantly zyada hai ya nahi.

### 3. Isse Kya Hua / Benefit Kya Mila? (What did it achieve?)
Is table ke bina koi bhi mathematical test (ROR, PRR, Bayesian IC) run nahi ho sakta. Ye saare statistical calculations ka foundation (input) hai.

### 4. Interview me Kaise Bolna Hai?
> *"Step 6 was constructing the 2x2 Contingency Matrix. I categorized the entire database into counts A, B, C, and D to measure the target drug-event co-occurrence against the general background of all other drugs."*

---

## STEP 7: Frequentist Analysis Engine (ROR, PRR, Haldane, Fisher, Chi2)

### 1. Humne Kya Kiya? (What did we do in code?)
$A, B, C, D$ aate hi humne classical disproportionality metrics calculate kiye:
1. **ROR (Reporting Odds Ratio):** $\frac{A \cdot D}{B \cdot C}$ $\rightarrow$ Batata hai kitne गुना (times) odds zyada hain.
2. **PRR (Proportional Reporting Ratio):** $\frac{A / (A+B)}{(A+C) / N}$ $\rightarrow$ FDA/EMA ka standard ratio.
3. **Haldane’s Odds Ratio:** Agar $A=0$ hai to math division-by-zero crash hone se bachane ke liye $+0.5$ add karke $(\frac{A+0.5}{B+0.5}) / (\frac{C+0.5}{D+0.5})$ calculate karta hai.
4. **Fisher’s Exact Test $p$-value:** Small counts ($A < 5$) ke liye exact hypergeometric probability nikalta hai.
5. **Yates Chi-Square ($\chi^2$):** Goodness-of-fit test jo small sample size overestimation ko rokne ke liye $|AD - BC| - N/2$ subtract karta hai.

### 2. Wo Hota Kya Hai? (What is it in simple terms?)
Ye humara **Fast Screening Engine** hai. Ye jaldi se saare metrics calculate karke batata hai ki kya target drug me reaction ka percentage normal background se zyada hai.

### 3. Isse Kya Hua / Benefit Kya Mila? (What did it achieve?)
- FDA/EMA regulatory guidelines ke mutabiq agar $A \ge 3$, $\text{PRR} \ge 2.0$, aur $\chi^2 \ge 4.0$ hai, to initial safety alert flag ho jaata hai.

### 4. Interview me Kaise Bolna Hai?
> *"Step 7 was the Frequentist Analysis Engine. I computed ROR, PRR, Haldane’s OR for zero-count correction, Fisher's Exact p-values, and Yates-corrected Chi-Square. This provided rapid, standard regulatory screening against FDA/EMA benchmarks."*

---

## STEP 8: Bayesian Validation Engine (WHO BCPNN IC & Beta Monte Carlo)

### 1. Humne Kya Kiya? (What did we do in code?)
- **BCPNN Information Component (IC):** $\text{IC} = \log_2 \left( \frac{A_{\text{obs}}}{E} \right)$ calculate kiya (WHO UMC metric).
- **Empirical Bayes Monte Carlo:** SciPy/NumPy se Beta distributions $s_1 \sim \text{Beta}(1+A, 1+B)$ aur $s_2 \sim \text{Beta}(1+C, 1+D)$ se **50,000 random simulations** run karke exact probability nikali ($P(\text{PRR} > 1)$).

### 2. Wo Hota Kya Hai? (What is it in simple terms?)
**Why Bayesian over ROR? (Small-Count Noise Trap)**
Mano ek nayi dava ke poore FAERS me **sirf 2 reports** aaye hain. Kismat se 1 report Nausea ki hai ($A=1, B=1, C=1000, D=1000000$).
Classical ROR formula lagane par ROR = **1,000x HIGHER RISK!** dikhayega. Lekin ye 1 report sirf ek random coincidental noise ho sakti hai!

**Bayesian Solution ("Shrinkage"):**
Bayesian algorithm pehle se ek Prior Expectation maan kar chalta hai ki zyadatar dava-reaction pairs me koi rishta nahi hota.
- Jab sample $A$ chhota hota hai ($A=1$), Bayesian model us number ko **khinch kar neeche (shrinkage)** baseline $1.0$ par le aata hai taaki false alarm na baje.
- Jab sample $A$ bada hota hai ($A=100$), real data prior ko override kar deta hai aur True Signal confirm ho jaata hai!

### 3. Isse Kya Hua / Benefit Kya Mila? (What did it achieve?)
- Random noise par lakho rupaye waste hone se bach gaye (False Positives eliminate ho gaye).
- Business leadership ko exact confidence level mil gaya (jaise: *"98.7% Probability that risk > 1"*).

### 4. Interview me Kaise Bolna Hai?
> *"Step 8 was the Bayesian Validation Engine. Classical ROR explodes on small sample sizes (A < 5), producing false positives. I implemented WHO BCPNN Information Component and ran 50,000 Beta-distribution Monte Carlo simulations. Bayesian shrinkage pulls low-count noise back toward baseline, ensuring we only confirm statistically robust signals."*

---

## STEP 9: Real Case Study Results (Capivasertib & Stomatitis)

### 1. Humne Kya Numbers Dekhe?
Capivasertib (Truqap) drug par jab humne pipeline chalayi:
- $A = 24$ cases (Capivasertib + Stomatitis co-occurrence)
- $ROR = 1.58$ ($95\%\text{ CI: } 1.06 - 2.38$)
- Fisher $p$-value $= 0.0373$ ($p < 0.05$)
- Yates Chi-Square $= 4.49$ ($p = 0.0341$)
- Bayesian IC $= 0.68$ ($\text{IC}_{2.5} > 0$)
- Bayesian Monte Carlo Probability $P(\text{PRR} > 1) = \mathbf{98.7\%}$

### 2. Simple Output Meaning
Capivasertib lene wale patients ko Stomatitis (mouth ulcers) hone ke **58% higher odds** hain background population ke muqable ($ROR = 1.58$), aur **98.7% Bayesian probability** hai ki ye koi random noise nahi balki ek real safety signal hai.

---

## STEP 10: Executive Output & Business Recommendations

### 1. Humne Output me Kya Banaya?
- **Multi-Sheet Excel (`FAERS_Results.xlsx`):** `Summary` sheet me overall statistics aur `Event_Synonym_Breakdown` me individual terms ke counts.
- **Audit CSV (`csv_log_output.csv`):** Skipped lines ka log.

### 2. Executive Leadership ko Kya Actionable Advice Denge?
1. **Drug Label Update:** Drug ke prescribing box insert me Section 6 (Adverse Reactions) me Stomatitis ka warning add karo.
2. **Physician Guidance:** Oncologists ko advise karo ki Capivasertib start karte hi patients ko oral antiseptic mouthwash prescribe karein.
3. **Proactive Regulatory Filing:** FDA/EMA ko proactive Risk Management Plan (RMP) update submit karo taaki regulatory warning letters se bacha jaa sake.
4. **Litigation Defense:** Company ko unflagged patient lawsuits se bachane ke liye documentation maintain karo.

---

## Chapter 11: Summary Comparison Table (Cheat-Sheet for Quick Revision)

| Step Name | What it is | Why we did it | What it achieved |
| :--- | :--- | :--- | :--- |
| **1. Data Ingestion** | Reading ASCII/Excel text files | Multi-quarter files automated loading | 11.6M Drug & 8.7M Reaction rows loaded in memory |
| **2. Encoding Resilience** | UTF-8 / Latin-1 fallback loader | Prevents crashes on global corrupt text | 100% pipeline stability, 0 crashes, audit log saved |
| **3. Primary Suspect Filter** | Filtering `role_cod == 'PS'` | Removes harmless background medications | Isolates causal drug, prevents noise explosion |
| **4. VigiMatch Dedup** | Composite keys + SHA-256 hashing | Eliminates duplicate reports for same patient | 13k–23k duplicate records dropped per quarter |
| **5. Synonym Normalization** | Brand $\rightarrow$ Generic & PT grouping | Solves signal dilution | Combines 3 weak counts of 100 into 1 strong 300 signal |
| **6. 2x2 Matrix ($A,B,C,D$)** | Cross-tabulation co-occurrence table | Foundation for all statistical formulas | Compares target drug vs database background |
| **7. Frequentist Engine** | ROR, PRR, Haldane, Fisher, Chi2 | Fast initial regulatory screening | Flags initial alerts based on FDA/EMA benchmarks |
| **8. Bayesian Engine** | WHO BCPNN IC + Beta Monte Carlo | Prevents false alarms on small counts ($A < 5$) | Applies shrinkage, gives exact posterior probabilities |
| **9. Case Study** | Capivasertib & Stomatitis run | Real-world validation | ROR 1.58, $P(\text{PRR}>1) = 98.7\%$ verified signal |
| **10. Business Action** | Excel Export & Strategy Plan | Translates data into business value | Label updates, FDA RMP filings, litigation defense |
