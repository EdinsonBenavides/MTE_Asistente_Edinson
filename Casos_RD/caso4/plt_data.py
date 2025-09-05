import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset

def tiempo_convergencia(datos, tolerancia=0.02):
    """
    Calcula el tiempo de convergencia como el número de iteraciones
    que toma el algoritmo para llegar a una franja del ±2% del valor final.
    
    Parámetros:
        datos (list or np.array): Lista con los valores del proceso.
        tolerancia (float): Porcentaje de tolerancia (por defecto 0.02 -> 2%).

    Retorna:
        int: Índice de la iteración donde se alcanza la convergencia.
    """
    valor_final = datos[-1]
    margen_inferior = valor_final * (1 - tolerancia)
    margen_superior = valor_final * (1 + tolerancia)

    for i in range(len(datos)):
        # Verifica si desde este punto en adelante todos los valores están dentro del margen
        if all(margen_inferior <= x <= margen_superior for x in datos[i:]):
            return i  # Esta es la iteración en la que se alcanza la convergencia

    return -1  # No converge dentro de la tolerancia


def calcular_itse(x_ref, x_iteraciones):
    """
    Calcula el ITSE para una secuencia de vectores de estado.
    
    Parámetros:
    - x_ref: vector objetivo (numpy array)
    - x_iteraciones: lista o array de vectores de estado en el tiempo (list of numpy arrays)

    Retorna:
    - ITSE: valor numérico del Integral del Tiempo por el Error al Cuadrado
    """
    itse = 0.0
    for t, x_t in enumerate(x_iteraciones):
        error = x_ref - x_t
        itse += t * np.linalg.norm(error) ** 2
    return itse


df1 = pd.read_csv('agente1/evolution_data.csv')
df2 = pd.read_csv('agente2/evolution_data.csv')
df3 = pd.read_csv('agente3/evolution_data.csv')
df4 = pd.read_csv('agente4/evolution_data.csv')
df5 = pd.read_csv('agente5/evolution_data.csv')
df6 = pd.read_csv('agente6/evolution_data.csv')
optimal_values = [280.7,82.0,197.062,151.425,60.00,378.811]

f1 = list(df1["Fitness"])
f2 = list(df2["Fitness"])
f3 = list(df3["Fitness"])
f4 = list(df4["Fitness"])
f5 = list(df5["Fitness"])
f6 = list(df6["Fitness"])

p1 = list(df1["Potencia"])
p2 = list(df2["Potencia"])
p3 = list(df3["Potencia"])
p4 = list(df4["Potencia"])
p5 = list(df5["Potencia"])
p6 = list(df6["Potencia"])

P = np.array([p1[:-2],p2[:-2],p3[:-2],p4[:-2],p5[:-2],p6[:-2]]).T

####### obtener la norma de la diferencia entre el vector de los velores 
####### teoricos y el de los obtenidos 

opti_P = [p1[-2],p2[-2],p3[-2],p4[-2],p5[-2],p6[-2]]

norm = np.linalg.norm(np.array(optimal_values) - np.array(opti_P))

####### Tiempo de convergencia
iter_convergencia = []
tiempo = []
for i in range(len(P[0])):
    iter_convergencia.append(tiempo_convergencia(list(P[:,i])))

prom_t_c = np.mean(np.array(iter_convergencia))
###### ITSE

itse4 = calcular_itse(optimal_values,P)

###### Restricciones 

sum_p = sum(opti_P)



plt.plot(p1,label="Agent 1")
plt.plot(p2,label="Agent 2")
plt.plot(p3,label="Agent 3")
plt.plot(p4,label="Agent 4")
plt.plot(p5,label="Agent 5")
plt.plot(p6,label="Agent 6")

plt.title("Power evolution ")
plt.xlabel("Iterations")
plt.ylabel("Power (kW)")
plt.xlim(-5,1700.1)
for i in range(len(optimal_values)):
    plt.axhline(y=optimal_values[i], color='gray', linestyle='--')
plt.legend(loc='upper right', frameon=True)
plt.savefig("Power evolution_4.pdf", dpi=1080)
plt.show()

plt.plot(f1,label="Agent 1")
plt.plot(f2,label="Agent 2")
plt.plot(f3,label="Agent 3")
plt.plot(f4,label="Agent 4")
plt.plot(f5,label="Agent 5")
plt.plot(f6,label="Agent 6")

plt.title("Fitness evolution")
plt.legend(loc='lower right', frameon=True)
plt.xlabel("Iterations")
plt.ylabel("Fitness ($/kW)")
plt.xlim(-5,1700.1)
plt.savefig("Fitness evolution_4.pdf", dpi=1080)
plt.show()

