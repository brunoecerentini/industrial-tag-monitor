import sys
print("Python:", sys.version)

try:
    import pandas as pd
    print("Pandas OK:", pd.__version__)
except ImportError as e:
    print("Pandas ERRO:", e)

try:
    import openpyxl
    print("Openpyxl OK:", openpyxl.__version__)
except ImportError as e:
    print("Openpyxl ERRO:", e)

# Teste basico
print("\nTestando leitura do taglist.csv...")
try:
    df = pd.read_csv('taglist.csv')
    print(f"Arquivo lido com sucesso: {len(df)} linhas")
    print(df.head(2))
except Exception as e:
    print(f"Erro ao ler: {e}")

# Teste escrita Excel
print("\nTestando escrita Excel...")
try:
    df_test = pd.DataFrame({'A': [1,2,3], 'B': ['x','y','z']})
    df_test.to_excel('test_output.xlsx', index=False)
    print("Excel escrito com sucesso!")
except Exception as e:
    print(f"Erro ao escrever Excel: {e}")

