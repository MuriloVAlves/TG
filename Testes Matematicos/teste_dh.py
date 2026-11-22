import sympy as sp

theta, phi, d, h, l = sp.symbols("theta phi d h l", real=True)


def dh(th, di, ai, al):
    return sp.Matrix(
        [
            [
                sp.cos(th),
                -sp.sin(th) * sp.cos(al),
                sp.sin(th) * sp.sin(al),
                ai * sp.cos(th),
            ],
            [
                sp.sin(th),
                sp.cos(th) * sp.cos(al),
                -sp.cos(th) * sp.sin(al),
                ai * sp.sin(th),
            ],
            [0, sp.sin(al), sp.cos(al), di],
            [0, 0, 0, 1],
        ]
    )


A01 = dh(theta, h, 0, sp.pi / 2)
A12 = dh(phi, -d, 0, 0)
A23 = dh(0, 0, l, 0)

T02 = sp.simplify(A01 * A12)
T03 = sp.simplify(T02 * A23)

print("T02:")
sp.pprint(T02)
print("\nPosicao da ponta em T03:")
p = sp.simplify(T03[:3, 3])
sp.pprint(p)

# Testes de sanidade
print("\nTeste 1 (theta=0, phi=0):")
sp.pprint(p.subs({theta: 0, phi: 0}))

print("\nTeste 2 (phi=pi/2):")
sp.pprint(sp.simplify(p.subs({phi: sp.pi / 2})))