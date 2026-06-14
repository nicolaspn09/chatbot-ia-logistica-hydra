from ConectaPG import ConectaPG

class ShipManager:
    
    def add_ship(self, imo, nome):
        """Adiciona um navio na tabela de monitoramento"""
        # Sanitização básica para evitar erros de SQL simples
        nome = nome.replace("'", "") 
        sql = f"""
            INSERT INTO hydra.monitoramento (imo, navio_nome) 
            VALUES ('{imo}', '{nome}') 
            ON CONFLICT (imo) DO NOTHING;
        """
        return ConectaPG(sql).conecta_pg_insert()

    def remove_ship(self, imo):
        """Remove um navio do monitoramento"""
        sql = f"DELETE FROM hydra.monitoramento WHERE imo = '{imo}';"
        return ConectaPG(sql).conecta_pg_insert()

    def list_ships(self):
        """Lista todos os navios monitorados"""
        # O main.py espera index 0 = Nome, index 1 = IMO. A ordem do SELECT importa!
        sql = "SELECT navio_nome, imo FROM hydra.monitoramento ORDER BY navio_nome ASC;"
        return ConectaPG(sql).conecta_pg()

    def get_ship_timeline(self, imo):
        """Busca o histórico recente de situações para a Opção 4"""
        sql = f"""
            SELECT 
                situacao, 
                to_char(data_hora_registro, 'DD/MM HH24:MI') as data_fmt,
                manobra
            FROM hydra.registros 
            WHERE imo = '{imo}' 
            ORDER BY data_hora_registro DESC 
            LIMIT 5;
        """
        return ConectaPG(sql).conecta_pg()

    def get_ship_details(self, imo):
        """Busca detalhes estáticos (Nome, Bandeira) para o cabeçalho do relatório"""
        sql = f"""
            SELECT navio, bandeira 
            FROM hydra.registros 
            WHERE imo = '{imo}' 
            LIMIT 1;
        """
        resultado = ConectaPG(sql).conecta_pg()
        # Retorna a primeira linha se existir, ou None
        return resultado[0] if resultado else None