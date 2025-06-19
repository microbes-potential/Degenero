import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# --- Normalization Functions ---
def normalize_transcriptomics(df):
    return np.log2(df + 1)

def normalize_metabolomics(df):
    return np.log10(df + 1)

def normalize_lipidomics(df):
    return (df - df.mean()) / df.std()

def normalize_minmax(df):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df.fillna(0))
    return pd.DataFrame(scaled, columns=df.columns)

def normalize_standard(df):
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df.fillna(0))
    return pd.DataFrame(scaled, columns=df.columns)

# --- Missing Value Handling ---
def handle_missing_values(df, method='mean'):
    if method == 'mean':
        return df.fillna(df.mean())
    elif method == 'median':
        return df.fillna(df.median())
    elif method == 'drop':
        return df.dropna()
    else:
        return df

# --- PCA Analysis ---
def perform_pca(df, n_components=2):
    df = df.dropna(axis=1, how='any')  # Drop columns with missing values
    pca = PCA(n_components=n_components)
    components = pca.fit_transform(df)
    return pd.DataFrame(components, columns=[f'PC{i+1}' for i in range(n_components)])

# --- Volcano Plot Helper (Optional) ---
def generate_volcano_data(df, group1_idx, group2_idx, threshold_p=0.05, threshold_fc=1.5):
    from scipy.stats import ttest_ind
    pvals = []
    fold_changes = []
    for feature in df.columns:
        group1 = df.iloc[group1_idx][feature]
        group2 = df.iloc[group2_idx][feature]
        stat, pval = ttest_ind(group1, group2, equal_var=False)
        fold_change = group1.mean() / (group2.mean() + 1e-9)
        pvals.append(pval)
        fold_changes.append(fold_change)
    volcano_df = pd.DataFrame({'Feature': df.columns,
                               'p-value': pvals,
                               'FoldChange': fold_changes})
    volcano_df['-log10(p-value)'] = -np.log10(volcano_df['p-value'])
    volcano_df['Significant'] = (volcano_df['p-value'] < threshold_p) & (abs(volcano_df['FoldChange']) > threshold_fc)
    return volcano_df

