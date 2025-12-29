# -*- coding: utf-8 -*-
"""
Script para converter taglist.csv para o template padrao de criacao de tags da Deloitte (IP21).
"""

import os
import sys

# Diretorio base
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'conversion_log.txt')

def log(msg):
    """Escreve mensagem no log e console."""
    try:
        print(msg)
    except:
        pass
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(str(msg) + '\n')

# Limpar log anterior
with open(LOG_FILE, 'w', encoding='utf-8') as f:
    f.write("=== Log de Conversao ===\n")

try:
    log("Iniciando script...")
    log(f"Python version: {sys.version}")
    log(f"Diretorio: {SCRIPT_DIR}")
    
    import pandas as pd
    log(f"Pandas importado: {pd.__version__}")
    
    try:
        import openpyxl
        log(f"Openpyxl importado: {openpyxl.__version__}")
        CAN_EXCEL = True
    except ImportError:
        log("Openpyxl nao encontrado - salvando como CSV")
        CAN_EXCEL = False

except Exception as e:
    log(f"Erro na inicializacao: {e}")
    sys.exit(1)


def determine_data_type(tag_name):
    """Determina o tipo de dados baseado no nome da tag."""
    tag_lower = tag_name.lower()
    
    # Tags de texto (strings)
    text_tags = ['texto', 'observacao', 'hibrido', 'lavoura', 'segregacao', 'fertilidade']
    time_tags = ['hora_inic', 'hora']
    
    for text_tag in text_tags:
        if text_tag in tag_lower:
            return {'Data Type': 'String', 'Record Definition': 'IP_TextDef', 'ValueFormat': 'STRING', 'EngUnits': ''}
    
    for time_tag in time_tags:
        if time_tag in tag_lower:
            return {'Data Type': 'String', 'Record Definition': 'IP_TextDef', 'ValueFormat': 'STRING', 'EngUnits': ''}
    
    if 'temperatura' in tag_lower:
        return {'Data Type': 'Float', 'Record Definition': 'IP_Analogdef', 'ValueFormat': 'F6.1', 'EngUnits': 'C'}
    
    if 'umidade' in tag_lower:
        return {'Data Type': 'Float', 'Record Definition': 'IP_Analogdef', 'ValueFormat': 'F6.1', 'EngUnits': '%'}
    
    if 'altura' in tag_lower:
        return {'Data Type': 'Float', 'Record Definition': 'IP_Analogdef', 'ValueFormat': 'F6.2', 'EngUnits': 'm'}
    
    if 'peso' in tag_lower:
        return {'Data Type': 'Float', 'Record Definition': 'IP_Analogdef', 'ValueFormat': 'F10.2', 'EngUnits': 'kg'}
    
    return {'Data Type': 'Float', 'Record Definition': 'IP_Analogdef', 'ValueFormat': 'F6.2', 'EngUnits': ''}


def build_ip21_tagname(row):
    """Constroi o nome da tag IP21."""
    parts = []
    for col in ['Channel', 'Device', 'Pasta1', 'Pasta2', 'Pasta3', 'Tag_name']:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            parts.append(str(row[col]).strip())
    return '.'.join(parts)


def build_description(row):
    """Constroi a descricao da tag."""
    parts = []
    for col in ['Channel', 'Device', 'Pasta1', 'Pasta2', 'Tag_name']:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            parts.append(str(row[col]).strip())
    return ' - '.join(parts)


def convert_taglist_to_deloitte(input_file, output_file, use_case='Custom', 
                                 repository='TSK_DHIS_FMA1', prefix='Dataservers/RSLE::',
                                 dc_significance='1.00', dc_max_time_int='+000:05:00.0', 
                                 compression='ON'):
    """Converte o arquivo taglist.csv para o formato do template Deloitte IP21."""
    
    log(f"Lendo arquivo: {input_file}")
    df_input = pd.read_csv(input_file)
    log(f"{len(df_input)} tags encontradas")
    
    output_rows = []
    
    for idx, row in df_input.iterrows():
        tag_name = str(row['Tag_name']) if pd.notna(row['Tag_name']) else ''
        data_info = determine_data_type(tag_name)
        
        ip21_tagname = build_ip21_tagname(row)
        description = build_description(row)
        plc_tag = str(row['Hibrido']).strip() if pd.notna(row['Hibrido']) else ''
        opc_tag = f"{prefix}{plc_tag}" if plc_tag else ''
        
        # Define limites
        if data_info['Data Type'] == 'Float':
            maximum = '100000' if 'peso' in tag_name.lower() else '1000'
            minimum = '-50' if 'temperatura' in tag_name.lower() else '0'
        else:
            maximum = ''
            minimum = ''
        
        output_row = {
            'Use Case': use_case,
            'IP21 TagName': ip21_tagname,
            'Data Type': data_info['Data Type'],
            'Record Definition': data_info['Record Definition'],
            'Description': description,
            'Existing in IP21': 'NO',
            'PLC Tag Updates': 'Initial Build',
            'EngUnits': data_info['EngUnits'],
            'ValueFormat': data_info['ValueFormat'],
            'Repository': repository,
            'PLC TAG': plc_tag,
            'Prefix': prefix,
            'OPCTag': opc_tag,
            'IP_DC_SIGNIFICANCE': dc_significance if data_info['Data Type'] != 'String' else '',
            'IP_DC_MAX_TIME_INT': dc_max_time_int,
            'IP_COMPRESSION': compression,
            'maximum': maximum,
            'minimum': minimum,
            'Low Low Limit': '',
            'Low Limit': '',
            'High Limit': '',
            'High High Limit': ''
        }
        output_rows.append(output_row)
    
    df_output = pd.DataFrame(output_rows)
    
    # Salva arquivo
    if output_file.endswith('.xlsx') and CAN_EXCEL:
        df_output.to_excel(output_file, index=False, sheet_name='Tags')
        log(f"Arquivo Excel salvo: {output_file}")
    else:
        csv_file = output_file.replace('.xlsx', '.csv')
        df_output.to_csv(csv_file, index=False)
        log(f"Arquivo CSV salvo: {csv_file}")
    
    log(f"Conversao concluida! {len(df_output)} tags processadas")
    log(f"\nResumo por tipo de dados:")
    log(df_output['Data Type'].value_counts().to_string())
    
    return df_output


def main():
    """Funcao principal."""
    try:
        INPUT_FILE = os.path.join(SCRIPT_DIR, 'taglist.csv')
        OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'tags_deloitte_output.xlsx')
        
        log("=" * 60)
        log("Conversor TagList -> Template Deloitte IP21")
        log("=" * 60)
        
        if not os.path.exists(INPUT_FILE):
            log(f"ERRO: Arquivo nao encontrado: {INPUT_FILE}")
            return
        
        df_result = convert_taglist_to_deloitte(
            input_file=INPUT_FILE,
            output_file=OUTPUT_FILE,
            use_case='Custom',
            repository='TSK_DHIS_FMA1',
            prefix='Dataservers/RSLE::'
        )
        
        log("\n" + "=" * 60)
        log("Processo finalizado com sucesso!")
        log("=" * 60)
        
        log("\nPreview das primeiras 5 tags:")
        log(df_result[['IP21 TagName', 'Data Type', 'Description']].head().to_string())
        
    except Exception as e:
        log(f"ERRO durante execucao: {e}")
        import traceback
        log(traceback.format_exc())


if __name__ == '__main__':
    main()
