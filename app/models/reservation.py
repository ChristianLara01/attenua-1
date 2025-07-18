"""
Modelo para gerenciamento de reservas.
"""
import secrets
from typing import Dict, Optional
from datetime import datetime
import logging
from .cabin import cabin_service

logger = logging.getLogger(__name__)

class ReservationService:
    """Serviço para operações com reservas."""
    
    def __init__(self):
        self.cabin_service = cabin_service
    
    def generate_unique_code(self) -> str:
        """Gera um código único para a reserva."""
        max_attempts = 10
        
        for _ in range(max_attempts):
            code = secrets.token_hex(3)  # 6 caracteres hexadecimais
            
            # Verifica se o código já existe
            if not self.cabin_service.find_reservation_by_code(code):
                return code
        
        # Se não conseguir gerar um código único, adiciona timestamp
        timestamp = str(int(datetime.now().timestamp()))[-3:]
        return f"{secrets.token_hex(2)}{timestamp}"
    
    def validate_reservation_data(self, data: Dict) -> Dict:
        """
        Valida os dados da reserva.
        Retorna dicionário com 'valid' (bool) e 'errors' (list).
        """
        errors = []
        
        # Validação de campos obrigatórios
        required_fields = ['cabin_id', 'date_iso', 'slot', 'first_name', 'last_name', 'email']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Campo '{field}' é obrigatório")
        
        # Validação de formato de email (básica)
        email = data.get('email', '')
        if email and '@' not in email:
            errors.append("Formato de email inválido")
        
        # Validação de data (formato YYYY-MM-DD)
        date_iso = data.get('date_iso', '')
        if date_iso:
            try:
                datetime.strptime(date_iso, '%Y-%m-%d')
            except ValueError:
                errors.append("Formato de data inválido (use YYYY-MM-DD)")
        
        # Validação de horário (formato HH:MM)
        slot = data.get('slot', '')
        if slot:
            try:
                datetime.strptime(slot, '%H:%M')
            except ValueError:
                errors.append("Formato de horário inválido (use HH:MM)")
        
        # Validação de cabin_id
        cabin_id = data.get('cabin_id')
        if cabin_id:
            try:
                cabin_id = int(cabin_id)
                cabin = self.cabin_service.get_cabin_by_id(cabin_id)
                if not cabin:
                    errors.append("Cabine não encontrada")
            except (ValueError, TypeError):
                errors.append("ID da cabine deve ser um número")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def check_availability(self, cabin_id: int, date_iso: str, slot: str) -> bool:
        """Verifica se uma cabine está disponível em um horário específico."""
        available_cabins = self.cabin_service.find_available_cabins(date_iso, slot)
        return any(cabin['id'] == cabin_id for cabin in available_cabins)
    
    def create_reservation(self, data: Dict) -> Dict:
        """
        Cria uma nova reserva.
        Retorna dicionário com 'success' (bool), 'code' (str) e 'message' (str).
        """
        try:
            # Validação dos dados
            validation = self.validate_reservation_data(data)
            if not validation['valid']:
                return {
                    'success': False,
                    'code': None,
                    'message': f"Dados inválidos: {', '.join(validation['errors'])}"
                }
            
            cabin_id = int(data['cabin_id'])
            date_iso = data['date_iso']
            slot = data['slot']
            
            # Verifica disponibilidade
            if not self.check_availability(cabin_id, date_iso, slot):
                return {
                    'success': False,
                    'code': None,
                    'message': "Cabine não disponível no horário selecionado"
                }
            
            # Gera código único
            unique_code = self.generate_unique_code()
            
            # Cria dados da reserva
            reservation_data = {
                "dia": date_iso,
                "hora": slot,
                "qtde_horas": 1,
                "id_usuario": data['email'],
                "first_name": data['first_name'],
                "last_name": data['last_name'],
                "senha_unica": unique_code,
                "created_at": datetime.now().isoformat(),
                "status": "confirmed"
            }
            
            # Adiciona reserva à cabine
            success = self.cabin_service.add_reservation(cabin_id, reservation_data)
            
            if success:
                logger.info(f"Reserva criada: {unique_code} para cabine {cabin_id}")
                return {
                    'success': True,
                    'code': unique_code,
                    'message': "Reserva criada com sucesso"
                }
            else:
                return {
                    'success': False,
                    'code': None,
                    'message': "Erro interno ao criar reserva"
                }
                
        except Exception as e:
            logger.error(f"Erro ao criar reserva: {e}")
            return {
                'success': False,
                'code': None,
                'message': "Erro interno do servidor"
            }
    
    def verify_reservation_code(self, code: str) -> Dict:
        """
        Verifica um código de reserva.
        Retorna dicionário com informações da verificação.
        """
        try:
            reservation = self.cabin_service.find_reservation_by_code(code)
            
            if not reservation:
                return {
                    'valid': False,
                    'message': "Código não encontrado",
                    'cabin_id': None
                }
            
            # Verifica se é o horário correto (implementação simplificada)
            # Em produção, seria necessário verificar timezone e horário exato
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%H:%M')
            
            reservation_date = reservation.get('dia')
            reservation_time = reservation.get('hora')
            
            # Para demonstração, aceita qualquer horário do dia atual
            if reservation_date == current_date:
                return {
                    'valid': True,
                    'message': "Código válido",
                    'cabin_id': reservation.get('cabin_id'),
                    'reservation': reservation
                }
            else:
                return {
                    'valid': False,
                    'message': "Código expirado ou fora do horário",
                    'cabin_id': reservation.get('cabin_id')
                }
                
        except Exception as e:
            logger.error(f"Erro ao verificar código: {e}")
            return {
                'valid': False,
                'message': "Erro interno do servidor",
                'cabin_id': None
            }
    
    def get_reservation_summary(self, cabin_id: int, date_iso: str, slot: str) -> Dict:
        """Retorna resumo da reserva para exibição."""
        cabin = self.cabin_service.get_cabin_by_id(cabin_id)
        
        if not cabin:
            return {}
        
        return {
            'cabin_id': cabin_id,
            'cabin_name': cabin.get('nome', f'Cabine {cabin_id}'),
            'date_iso': date_iso,
            'slot': slot,
            'price': cabin.get('valor_hora', 0),
            'capacity': cabin.get('capacidade', 1),
            'description': cabin.get('descricao', '')
        }

# Instância global do serviço
reservation_service = ReservationService()

