from fenics import *
import matplotlib.pyplot as plt

# 2D 영역 생성 (1x1 크기)
mesh = UnitSquareMesh(32, 32)

# 함수 공간 정의
V = FunctionSpace(mesh, 'P', 1)

# 경계 조건 정의
u_D = Expression('x[0]*x[1]', degree=2)

def boundary(x, on_boundary):
    return on_boundary

bc = DirichletBC(V, u_D, boundary)

# 문제 설정
u = TrialFunction(V)
v = TestFunction(V)
f = Constant(-6.0)
a = dot(grad(u), grad(v)) * dx
L = f * v * dx

# 방정식 풀이
u = Function(V)
solve(a == L, u, bc)

# 결과 시각화
plot(u)
plt.show()
