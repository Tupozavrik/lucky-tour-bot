class UonMockService:
    @staticmethod
    async def get_user_destination(uon_id: str) -> str:
        """
        Реализация-заглушка (mock).
        В реальном сценарии здесь будет выполняться API запрос к U-ON 
        с использованием config.UON_API_KEY и переданного uon_id.
        """
        # В целях тестирования предполагаем, что конкретные uon_ids означают конкретные направления.
        # Но в целом, мы просто вернем 'Turkey' для любого похожего на валидный id (числового).
        
        if uon_id.strip() == "123":
            return "Egypt"
        elif uon_id.strip().isdigit():
            return "Turkey"
        
        # None подразумевает недействительность или отсутствие направления
        return None
