class SimulationState:
    """Clase simple para almacenar parámetros globales de la simulación.

    Uso:
        from simulation_state import SimulationState
        SimulationState.set_total_buildings(50)
        n = SimulationState.get_total_buildings()
    """
    total_buildings = None

    @classmethod
    def set_total_buildings(cls, n: int):
        try:
            cls.total_buildings = int(n) if n is not None else None
        except Exception:
            cls.total_buildings = None

    @classmethod
    def get_total_buildings(cls):
        return cls.total_buildings
