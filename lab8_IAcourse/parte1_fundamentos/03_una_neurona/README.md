# 03 — Una neurona (perceptrón)

**Idea:** una neurona artificial multiplica cada entrada por un **peso**,
suma todo más un **sesgo**, y si el total pasa de 0 responde 1. Entrenarla
es ajustar los pesos cada vez que se equivoca.

```
x1 ──w1──┐
          ├─(suma + b)──> ¿> 0? ──> 1 ó 0
x2 ──w2──┘
```

```bash
python perceptron.py
```

## Qué observar

- **AND** y **OR** los aprende en pocas épocas.
- **XOR** (1 solo si las entradas son distintas) nunca llega a 4/4.
  Si dibujas los 4 puntos en un plano, los 1 quedan en esquinas opuestas:
  ninguna línea recta los separa, y una neurona sola solo sabe trazar una recta.

## Retos

1. Agrega la compuerta `"NAND"` (lo contrario de AND) a `TABLAS`. ¿La aprende?
2. Imprime `w1, w2, b` en cada época para ver cómo se van moviendo.

**Siguiente:** en [04](../04_red_neuronal/) juntamos varias neuronas y XOR se resuelve.
