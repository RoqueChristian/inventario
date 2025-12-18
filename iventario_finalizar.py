import pandas as pd
import oracledb
from dotenv import load_dotenv
import os



oracledb.init_oracle_client(lib_dir=r"C:\\instantclient_23_9")


load_dotenv()
user = os.getenv('user', '')
password = os.getenv('password', '')
dsn = '192.168.0.1/WINT'


# ----------------------------------------------------
# Consultas SQL 
# ----------------------------------------------------
sql_inventario_pendente_baixa = """
    SELECT M.CODFILIAL AS FILIAL
        , M.NUMNOTA AS INVENTARIO
        , TO_CHAR(M.DTMOV, 'DD/MM/YYYY') AS DATA_ATUALIZACAO
        , M.CODFUNCLANC AS CODIGO_USUARIO
        , (SELECT NOME FROM PCEMPR WHERE MATRICULA = M.CODFUNCLANC AND ROWNUM = 1) AS NM_USUARIO_ATUALIZACAO
        , MAX(NVL(M.NUMTRANSENT, 0)) AS TRANSACAO_ENT
        , MAX(NVL(M.NUMTRANSVENDA, 0)) AS TRANSACAO_SAIDA
        -- Aplicamos o SUM para totalizar os itens da nota no agrupamento
        , ROUND(SUM((NVL(M.PUNIT, 0) + NVL(M.VLOUTRASDESP, 0) + NVL(M.VLFRETE_RATEIO, 0) +
                NVL(M.VLOUTROS, 0) + NVL(M.VLIPI, 0) + NVL(M.ST, 0) - NVL(M.VLREPASSE, 0)) * NVL(M.QT, 0)), 2) 
        AS VALOR
    FROM PCMOV M
    WHERE M.NUMNOTA IS NOT NULL
    AND M.CODOPER IN ('EI', 'SI')
    AND M.STATUS = 'B'
    AND NVL(M.QT, 0) > 0
    AND M.DTCANCEL IS NULL
    AND M.DTMOV BETWEEN TO_DATE('2025-10-01', 'YYYY-MM-DD') AND TO_DATE('2025-12-17', 'YYYY-MM-DD')
    --AND M.CODFILIAL = '5'
    AND NOT EXISTS (SELECT 1
                        FROM PCMOVCOMPLE MC
                        JOIN PCMOV P2 ON P2.NUMTRANSITEM = MC.NUMTRANSITEM
                        WHERE MC.NUMINVENT = M.NUMNOTA
                        --AND P2.CODFILIAL = '5'
                        AND P2.CODOPER IN ('EI', 'SI', 'EA', 'SA')
                        AND P2.STATUS = 'A'
                        AND P2.DTMOV >= TO_DATE('2025-10-01', 'YYYY-MM-DD')
                        AND P2.CODPROD = M.CODPROD
                        AND P2.DTCANCEL IS NULL)
    GROUP BY M.CODFILIAL
        , M.NUMNOTA
        , M.STATUS
        , M.DTMOV 
        , M.CODFUNCLANC
    ORDER BY M.CODFILIAL
        , M.DTMOV DESC
        , M.NUMNOTA DESC
"""


print("Tentando conectar ao banco de dados Oracle...")
try:
    with oracledb.connect(user=user, password=password, dsn=dsn) as connection:
        print("Conexão bem-sucedida. Executando consultas...")

        # 1. Carregar Dados
        df_inventario_pendete_baixa = pd.read_sql(sql_inventario_pendente_baixa, con=connection)

        NOME_ARQUIVO = 'acompanhamento_inventario_pendente_baixa.csv'

        df_inventario_pendete_baixa.to_csv(
            NOME_ARQUIVO, 
            index=False, 
            sep=';', 
            encoding='utf-8-sig',
            decimal=',' 
        )

        print("\nTabela final de Acompanhamento de Inventário criada e salva como 'acompanhamento_inventario_detalhado.csv'! ✅")

except oracledb.Error as e:
    error_obj, = e.args
    print(f"Erro ao se conectar com o banco Oracle: ORA-{error_obj.code}: {error_obj.message}")
except Exception as e:
    print(f"Ocorreu um erro: {e}")