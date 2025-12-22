# import pandas as pd
# import oracledb
# from dotenv import load_dotenv
# import os

# # Configuração Técnica
# oracledb.init_oracle_client(lib_dir=r"C:\\instantclient_23_9")
# load_dotenv()

# user = os.getenv('user', '')
# password = os.getenv('password', '')
# dsn = os.getenv('dsn', '192.168.0.1/WINT')

# def get_sql(operacao):
#     suffix = 'entrada' if operacao == 'EI' else 'saida'
#     return f"""
#     SELECT
#         M.codfilial, M.numnota AS numero_nota, M.codprod, P.descricao AS nome_produto, 
#         C.CATEGORIA AS categoria, TRUNC(M.dtmov) AS dtmov_{suffix}, 
#         SUM(M.qtcont) AS qtd_{suffix},
#         ROUND(SUM(M.punitcont * M.qtcont), 2) AS vlr_{suffix}
#     FROM pcmov M
#     LEFT JOIN pcprodut P ON P.codprod = M.codprod
#     LEFT JOIN pcdepto D ON D.CODEPTO = P.CODEPTO
#     LEFT JOIN PCSECAO S ON S.CODSEC = P.CODSEC AND S.codepto = D.codepto
#     LEFT JOIN pccategoria C ON C.CODCATEGORIA = P.CODCATEGORIA AND C.codsec = S.codsec
#     WHERE M.codoper = '{operacao}' AND EXTRACT(YEAR FROM M.dtmov) = 2025
#     GROUP BY M.codfilial, M.numnota, M.codprod, P.descricao, C.CATEGORIA, TRUNC(M.dtmov)
#     HAVING SUM(M.qtcont) <> 0
#     """

# sql_estoque = "SELECT codprod, codfilial, SUM(qtest) AS qtd_estoque_atual FROM pcest WHERE qtest > 0 GROUP BY codprod, codfilial"

# try:
#     with oracledb.connect(user=user, password=password, dsn=dsn) as conn:
#         print("Extraindo movimentações...")
#         df_ei = pd.read_sql(get_sql('EI'), con=conn)
#         df_si = pd.read_sql(get_sql('SI'), con=conn)
#         df_est = pd.read_sql(sql_estoque, con=conn)
        
#         # Merge com Estoque Atual
#         df_final_ei = pd.merge(df_ei, df_est, on=['CODFILIAL', 'CODPROD'], how='left')
#         df_final_si = pd.merge(df_si, df_est, on=['CODFILIAL', 'CODPROD'], how='left')

#         # Exportação
#         df_final_ei.to_csv('inventario_entrada.csv', index=False, sep=';', encoding='utf-8-sig', decimal=',')
#         df_final_si.to_csv('inventario_saida.csv', index=False, sep=';', encoding='utf-8-sig', decimal=',')
#         print("Arquivos CSV gerados com sucesso! ✅")
# except Exception as e:
#     print(f"Erro no processo de extração: {e}")