"""
Modelo para gerenciamento de cabines.
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging
from .database import db_manager

logger = logging.getLogger(__name__)

class CabinService:
    """Serviço para operações com cabines."""
    
    def __init__(self):
        self.collection = db_manager.cabines
        self._fallback_data = self._get_fallback_cabins()
    
    def _get_fallback_cabins(self) -> List[Dict]:
        """Dados de fallback para quando o MongoDB não estiver disponível."""
        return [
            {
                "id": 1,
                "nome": "Cabine A",
                "valor_hora": 25.00,
                "imagem": "cabin_a.webp",
                "descricao": "Cabine individual para trabalho focado",
                "capacidade": 1,
                "agendamentos": []
            },
            {
                "id": 2,
                "nome": "Cabine B",
                "valor_hora": 30.00,
                "imagem": "cabin_b.webp",
                "descricao": "Cabine para reuniões pequenas",
                "capacidade": 2,
                "agendamentos": []
            },
            {
                "id": 3,
                "nome": "Cabine C",
                "valor_hora": 35.00,
                "imagem": "cabin_c.webp",
                "descricao": "Cabine para equipes médias",
                "capacidade": 4,
                "agendamentos": []
            },
            {
                "id": 4,
                "nome": "Cabine D",
                "valor_hora": 40.00,
                "imagem": "cabin_d.png",
                "descricao": "Cabine premium para reuniões executivas",
                "capacidade": 6,
                "agendamentos": []
            }
        ]
    
    def get_all_cabins(self) -> List[Dict]:
        """Retorna todas as cabines disponíveis."""
        try:
            if self.collection is not None:
                cabins = list(self.collection.find({}, {"_id": 0}))
                if cabins:
                    return cabins
                else:
                    # Se não há cabines no banco, inicializa com dados padrão
                    self._initialize_default_cabins()
                    return self._fallback_data
            else:
                logger.warning("MongoDB não disponível, usando dados em memória")
                return self._fallback_data
                
        except Exception as e:
            logger.error(f"Erro ao buscar cabines: {e}")
            return self._fallback_data
    
    def _initialize_default_cabins(self):
        """Inicializa o banco com cabines padrão."""
        try:
            if self.collection is not None:
                self.collection.insert_many(self._fallback_data)
                logger.info("Cabines padrão inseridas no banco")
        except Exception as e:
            logger.error(f"Erro ao inicializar cabines padrão: {e}")
    
    def get_cabin_by_id(self, cabin_id: int) -> Optional[Dict]:
        """Retorna uma cabine específica por ID."""
        try:
            if self.collection is not None:
                cabin = self.collection.find_one({"id": cabin_id}, {"_id": 0})
                if cabin:
                    return cabin
            
            # Fallback para dados em memória
            for cabin in self._fallback_data:
                if cabin["id"] == cabin_id:
                    return cabin.copy()
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar cabine {cabin_id}: {e}")
            return None
    
    def find_available_cabins(self, date_iso: str, slot: str) -> List[Dict]:
        """
        Encontra cabines disponíveis para uma data e horário específicos.
        Usa agregação MongoDB para performance otimizada.
        """
        try:
            if self.collection is not None:
                # Pipeline de agregação otimizada
                pipeline = [
                    {
                        "$match": {
                            "agendamentos": {
                                "$not": {
                                    "$elemMatch": {
                                        "dia": date_iso,
                                        "hora": slot
                                    }
                                }
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "id": 1,
                            "nome": 1,
                            "valor_hora": 1,
                            "imagem": 1,
                            "descricao": 1,
                            "capacidade": 1
                        }
                    },
                    {
                        "$sort": {"id": 1}
                    }
                ]
                
                available = list(self.collection.aggregate(pipeline))
                if available:
                    return available
            
            # Fallback: verificação em memória
            available = []
            for cabin in self._fallback_data:
                is_available = True
                for agendamento in cabin.get("agendamentos", []):
                    if (agendamento.get("dia") == date_iso and 
                        agendamento.get("hora") == slot):
                        is_available = False
                        break
                
                if is_available:
                    cabin_copy = cabin.copy()
                    cabin_copy.pop("agendamentos", None)
                    available.append(cabin_copy)
            
            return available
            
        except Exception as e:
            logger.error(f"Erro ao buscar cabines disponíveis: {e}")
            return []
    
    def add_reservation(self, cabin_id: int, reservation_data: Dict) -> bool:
        """Adiciona uma reserva a uma cabine."""
        try:
            if self.collection is not None:
                result = self.collection.update_one(
                    {"id": cabin_id},
                    {"$push": {"agendamentos": reservation_data}}
                )
                return result.modified_count > 0
            else:
                # Fallback: adiciona à memória
                for cabin in self._fallback_data:
                    if cabin["id"] == cabin_id:
                        cabin["agendamentos"].append(reservation_data)
                        return True
                return False
                
        except Exception as e:
            logger.error(f"Erro ao adicionar reserva: {e}")
            return False
    
    def find_reservation_by_code(self, code: str) -> Optional[Dict]:
        """Encontra uma reserva pelo código único."""
        try:
            if self.collection is not None:
                cabin = self.collection.find_one(
                    {"agendamentos.senha_unica": code},
                    {"_id": 0, "id": 1, "agendamentos.$": 1}
                )
                
                if cabin and "agendamentos" in cabin:
                    reservation = cabin["agendamentos"][0]
                    reservation["cabin_id"] = cabin["id"]
                    return reservation
            else:
                # Fallback: busca em memória
                for cabin in self._fallback_data:
                    for agendamento in cabin.get("agendamentos", []):
                        if agendamento.get("senha_unica") == code:
                            agendamento["cabin_id"] = cabin["id"]
                            return agendamento
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar reserva por código: {e}")
            return None

# Instância global do serviço
cabin_service = CabinService()

