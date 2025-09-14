# Construcción de Compiladores — Workshop sobre Asignación de Registros y _Spilling_ con `obtenReg` (Solución)

**Integrantes:**

- Diego Pablo Valenzuela Palacios
- Gerson Alexander Ramirez Conoz
- Madeline Nahomy Castro Morales
- Aroldo Xavier López Osoy

---

## Objetivos de aprendizaje

- Comprender cómo `obtenReg` decide la asignación de registros y cuándo realizar _spilling_.
- Detectar por qué una mala gestión de registros provoca ineficiencias.
- Aplicar los criterios en ejemplos prácticos y resolver problemas.

---

## Ejemplo 1 — Sin _spilling_

**TAC:** `x = a + b`

**Idea:** si `a` ya reside en `R1` y `b` en `R2`, se reutilizan. De lo contrario, se cargan y se suma en un tercer registro:

```asm
# Caso general (si no están cargados):
LD R1, a
LD R2, b
ADD R3, R1, R2   # x = a + b (resultado en R3)
```

**Conclusión:** no se requiere _spilling_ porque hay registros suficientes y se prioriza la reutilización.

---

## Ejemplo 2 — Cuando no hay registros libres

**TAC:** `t = a - b` (con todos los registros ocupados)

**Estrategia de `obtenReg`:**

1. **Reutilización antes que _spilling_**

   - Si el valor ya está **también** en memoria (_clean_), se puede reutilizar su registro.
   - Si el valor **no se usará más adelante** (según análisis de vida útil), se reutiliza.
   - Si el valor **se puede recalcular** a bajo costo, se puede descartar y recomputar cuando sea necesario.

2. **Si nada de lo anterior aplica → _spilling_**  
   Elegir un candidato (p. ej., una temporal) y **guardar a memoria** para liberar un registro:

   ```asm
   ST t, R3        # Derrama el valor de R3 a memoria (t := R3)
   ```

3. **Realizar la operación con el registro liberado**
   ```asm
   SUB R3, R1, R2  # t = a - b, resultado en R3
   ```

---

# **Actividad — ¿Cómo decidir el Paso 1 de forma programática?**

Una implementación razonable en `obtenReg` puede seguir esta **política por prioridad**:

1. **Si la variable ya está en un registro**, devolverlo (0 costo).
2. **Si hay un registro libre**, asignarlo.
3. **Si no hay registros libres**, seleccionar víctima según estas heurísticas (en orden):
   - **No vivo / sin usos futuros**: elegir un registro cuyo valor **no aparezca** en usos futuros.
   - **En memoria y _clean_**: su valor ya está sincronizado en memoria (no requiere `ST`).
   - **Recomputable barato**: constantes, instrucciones triviales (ej.: `a+1`) o expresiones etiquetadas como “baratas”.
   - **Lejano próximo uso (Belady-like)**: si existe información de **próximo uso**, preferir el que **tarde más** en volver a usarse.
   - **LRU** como _fallback_ local: si no hay información de próximo uso, elegir el **menos recientemente usado**.
4. **Si la víctima está _dirty_** (no sincronizada) **y seguirá viva**, emitir `ST` antes de reasignar.
5. Asignar el registro liberado a la nueva variable y actualizar metadatos (vivos, próximo uso, _dirty_).

---

## Ejemplo 3 — _Spilling_ innecesario y mejora

**TAC original:**

```
t = a - b
u = a - c
v = t + u
a = d
d = v + u
```

# **Análisis del error**

- En el flujo defectuoso, se reservó `R3` para `t` y se forzó un _spilling_ temprano.
- Consecuencia: escrituras/lecturas a memoria evitables y más instrucciones.

# **Reescritura eficiente sin _spilling_ (solo 3 registros: R1–R3)**

**Idea clave:** **sobre-escribir** registros cuyos valores **no** se usarán más adelante y mantener en registros los valores con vida útil **más larga**.

```asm
# t = a - b
LD  R1, a           # R1 = a
LD  R2, b           # R2 = b
SUB R2, R1, R2      # R2 = t (= a - b)  ; b no se usa más → sobrescribir R2

# u = a - c
LD  R3, c           # R3 = c
SUB R1, R1, R3      # R1 = u (= a - c)  ; c no se usa más → R3 libre lógico tras el uso

# v = t + u
ADD R3, R2, R1      # R3 = v (= t + u)  ; R2=t, R1=u, R3=v

# a = d
LD  R2, d           # Reutiliza R2 para d (t ya no se usa)
ST  a, R2           # a := d

# d = v + u
ADD R2, R3, R1      # R2 = d (= v + u)
ST  d, R2           # d := R2
```

**Propiedad:** no se derraman temporales (`t`, `u`, `v`) a memoria; solo se hacen las asignaciones finales requeridas a `a` y `d`.
