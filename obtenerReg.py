class RegisterAllocator:
    def __init__(self):
        # Registros disponibles y mapeos
        self.registers = ["R1", "R2", "R3"]
        self.reg_to_var = {r: None for r in self.registers}
        self.var_to_reg = {}
        # "Memoria" simbólica donde caen los derrames
        self.memory = set()
        # Orden de asignación (para política FIFO)
        self.allocation_order = []

    def _find_free_register(self):
        for r in self.registers:
            if self.reg_to_var[r] is None:
                return r
        return None

    def get_register(self, variable: str) -> str:
        # Si ya está asignada, devolver el registro actual
        if variable in self.var_to_reg:
            return self.var_to_reg[variable]

        # Buscar registro libre
        free = self._find_free_register()
        if free is not None:
            # Asignar variable al registro libre
            self.reg_to_var[free] = variable
            self.var_to_reg[variable] = free
            self.allocation_order.append(variable)
            return free

        # No hay libres: derramar y asignar
        return self.spill_and_assign(variable)

    def spill_and_assign(self, variable: str) -> str:
        # Política FIFO: derramar la variable más antigua
        victim_var = self.allocation_order.pop(0)
        victim_reg = self.var_to_reg[victim_var]

        # "Guardar" a memoria simbólica
        self.memory.add(victim_var)

        # Liberar estructuras de mapeo
        del self.var_to_reg[victim_var]
        self.reg_to_var[victim_reg] = None

        # Asignar la nueva variable al registro liberado
        self.reg_to_var[victim_reg] = variable
        self.var_to_reg[variable] = victim_reg
        self.allocation_order.append(variable)
        return victim_reg

    def __str__(self) -> str:
        lines = ["<RegisterAllocator>"]
        lines.append("  Registros:")
        for r in self.registers:
            lines.append(f"    {r}: {self.reg_to_var[r]}")
        lines.append("  Memoria (derramados):")
        mem_list = ", ".join(sorted(self.memory)) if self.memory else "—"
        lines.append(f"    {mem_list}")
        return "\n".join(lines)


# Casos de prueba solicitados
if __name__ == '__main__':
    allocator = RegisterAllocator()
    print('a ->', allocator.get_register('a'))  # Esperado: R1
    print('b ->', allocator.get_register('b'))  # Esperado: R2
    print('c ->', allocator.get_register('c'))  # Esperado: R3
    print('d ->', allocator.get_register('d'))  # Esperado: derrama 'a' y asigna R1
    print(allocator)