# Pandas Data Exploration and Cleaning Assignment

This repository contains the complete solution for the **Basic Data Exploration and Cleaning using Pandas** assignment (Course: **Data Engineering 003**).

The objective is to perform data exploration, handle missing values, filter records, eliminate duplicates, create derived features, and export clean data using the Pandas library in Python.

---

## 📂 Repository Structure

* 📓 **[assignment_notebook.ipynb](file:///c:/Users/ASHMIT%20GUPTA/Desktop/assignmnet_1/assignment_notebook.ipynb)**: The core Jupyter Notebook containing fully executed Python code, visual tables, stdout outputs, and documentation for each step.
* 📊 **[cleaned_shopping_dataset.csv](file:///c:/Users/ASHMIT%20GUPTA/Desktop/assignmnet_1/cleaned_shopping_dataset.csv)**: The final cleaned, de-duplicated, and formatted dataset exported from Pandas.
* 📄 **[Combined_dataset.csv](file:///c:/Users/ASHMIT%20GUPTA/Desktop/assignmnet_1/Combined_dataset.csv)**: The primary combined shopping dataset loaded for exploration.
* 📦 **[archive.zip](file:///c:/Users/ASHMIT%20GUPTA/Desktop/assignmnet_1/archive.zip)**: The compressed archive containing the raw Kaggle dataset source.
* 🗂️ **Product-specific CSVs**: Individual category-wise datasets (e.g., `backpacks.csv`, `bedsheets.csv`, etc.) extracted from the source archive.

---

## 🛠️ Step-by-Step Methodology

### 1. Load Dataset
* Loaded the raw `Combined_dataset.csv` containing product listings from Myntra.
* Created a Pandas DataFrame to represent the structured tabular data.

### 2. Initial Data Exploration
* Used `head()` and `tail()` to view the leading and trailing rows.
* Extracted the shape of the dataset (`df.shape`) showing total entries and variables.
* Listed all column labels and inspected the automatically inferred data types (`dtypes`).

### 3. Handle Missing Values
* Identified columns containing missing values using `df.isnull().sum()`.
* Resolved missing values using specific domain-logical fallback strategies:
  * **`rating`**: Imputed with the dataset's **median rating** value.
  * **`ratings_count`**: Filled with `0` (assuming no ratings were recorded).
  * **`discount`**: Filled with `0` (indicating no discount applied).
  * **`seller_name`**: Imputed missing strings with `'Unknown Seller'`.
  * **`product_description`**: Filled missing descriptions with `'No description available'`.

### 4. Basic Data Operations
* **Filtering**: Filtered out high-value popular items where `rating > 4.5` and `ratings_count >= 50`.
* **Column Selection**: Selected a clean subset of metadata features (`product_id`, `title`, `rating`, `ratings_count`, `initial_price`, `category`) to work with.

### 5. Remove Duplicates
* Checked for duplicate products based on the unique `product_id` key.
* Removed duplicate rows using `df.drop_duplicates(subset=['product_id'], keep='first')` to maintain database integrity.

### 6. Derived Column Creation
* **Price Cleaning**: The raw `final_price` column contained currency symbols (`₹`), commas, quotes, and whitespace (e.g., `₹3,995.00`). Stripped formatting characters and parsed the values as numeric floats (`price`).
* **Quantity Generation**: Created a mock `quantity` column using `np.random.randint(1, 6)` for simulation purposes.
* **Calculation**: Generated a derived feature column: 
  $$\text{total\_amount} = \text{price} \times \text{quantity}$$

### 7. Export Cleaned Dataset
* Exported the fully cleaned DataFrame into `cleaned_shopping_dataset.csv` with formatting preserved and indices omitted.

---

## 🚀 Setup & Execution Instructions

Follow these instructions to set up the environment and run the notebook locally.

### Prerequisites

You need **Python 3.8+** installed. You can install the required libraries via `pip`:

```bash
pip install pandas numpy notebook
```

### Running the Notebook

1. Clone or download this repository to your local machine.
2. Open your terminal or Command Prompt in the repository folder.
3. Start the Jupyter Notebook interface:
   ```bash
   jupyter notebook
   ```
4. Click on `assignment_notebook.ipynb` in the browser dashboard and run the cells.
