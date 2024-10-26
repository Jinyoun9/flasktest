from flask import Flask, request, render_template
import pybamm
import numpy as np
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def run_pybaMM_simulation(active_material, charge_rate, discharge_rate, voltage_range, temperature, time, neg_electrode_capacity, pos_electrode_capacity, lithium_in_electrolyte):
    # 리튬 이온 배터리 모델 정의
    model = pybamm.lithium_ion.DFN()

    # 파라미터 값 설정 (활물질 데이터를 반영하여 사용)
    param = pybamm.ParameterValues(active_material)

    # 사용자 입력값을 반영한 추가 파라미터 설정
    custom_parameters = {
        "Total lithium in electrolyte [mol]": lithium_in_electrolyte,
        "Ambient temperature [K]": temperature,
        # 다른 사용자 정의 파라미터들 추가 가능
    }
    
    # 전극 용량은 직접적으로 존재하지 않으므로, 관련된 다른 파라미터를 조정하는 것이 필요합니다.
    # 파라미터 업데이트, 기본 파라미터에 없는 파라미터는 check_already_exists=False 사용
    param.update(custom_parameters, check_already_exists=False)

    # 실험 시나리오 설정: 충전/방전 속도, 구동 전압 범위, 온도 반영
    experiment = pybamm.Experiment(
        [
            (
                f"Discharge at {discharge_rate}C until {voltage_range[0]}V",
                f"Charge at {charge_rate}C until {voltage_range[1]}V",
                "Rest for 1 hour"
            )
        ],
        temperature=temperature  # 온도 반영
    )

    # 시뮬레이션 설정
    sim = pybamm.Simulation(model, experiment=experiment, parameter_values=param)
    sim.solve(t_eval=np.linspace(0, time, 1000))  # 시간 간격 설정

    # 시뮬레이션 결과에서 다양한 값 추출하여 반환
    solution = sim.solution
    time = solution["Time [h]"].entries
    voltage = solution["Terminal voltage [V]"].entries
    capacity_discharge = solution["Discharge capacity [A.h]"].entries
    throughput_capacity = solution["Throughput capacity [A.h]"].entries
    current = solution["Current [A]"].entries
    energy = solution["Discharge energy [W.h]"].entries

    # Charge capacity는 throughput에서 discharge 용량을 빼서 계산
    capacity_charge = np.array(throughput_capacity) - np.array(capacity_discharge)

    # SOC 계산 (음극에서 리튬의 비율)
    soc = solution["X-averaged negative particle surface concentration [mol.m-3]"].entries

    # 시간, 전압, 용량, 전류, SOC, 에너지를 리스트로 변환해 결과로 반환
    return {
        "time": time.tolist(),
        "voltage": voltage.tolist(),
        "capacity_discharge": capacity_discharge.tolist(),
        "capacity_charge": capacity_charge.tolist(),
        "current": current.tolist(),
        "soc": soc.tolist(),
        "energy": energy.tolist(),
    }


# 루트 경로 - 폼을 보여주는 페이지
@app.route('/')
def home():
    return render_template('index.html')

# 폼 제출 후 시뮬레이션을 실행하는 API
@app.route('/simulate', methods=['POST'])
def simulate():
    # 폼 데이터 받기
    active_material = request.form.get('active_material', 'Chen2020')  # 기본 활물질 데이터는 'Chen2020'
    charge_rate = float(request.form.get('charge_rate', 1))  # 기본 충전 속도 1C
    discharge_rate = float(request.form.get('discharge_rate', 1))  # 기본 방전 속도 1C
    voltage_min = float(request.form.get('voltage_min', 3.0))  # 구동 전압의 최소값
    voltage_max = float(request.form.get('voltage_max', 4.2))  # 구동 전압의 최대값
    temperature = float(request.form.get('temperature', 298.15))  # 기본 온도 (K)
    time = float(request.form.get('time', 3600))  # 시뮬레이션 시간
    neg_electrode_capacity = float(request.form.get('neg_electrode_capacity', 0.0))  # 음극 용량
    pos_electrode_capacity = float(request.form.get('pos_electrode_capacity', 0.0))  # 양극 용량
    lithium_in_electrolyte = float(request.form.get('lithium_in_electrolyte', 0.0))  # 전해질 내 리튬 양

    # PyBaMM 시뮬레이션 실행
    result = run_pybaMM_simulation(
        active_material, charge_rate, discharge_rate, (voltage_min, voltage_max), temperature, time, neg_electrode_capacity, pos_electrode_capacity, lithium_in_electrolyte
    )

    # zip 함수를 함께 전달
    return render_template(
        'result.html', 
        time=result["time"], 
        voltage=result["voltage"], 
        capacity_discharge=result["capacity_discharge"], 
        capacity_charge=result["capacity_charge"], 
        current=result["current"], 
        soc=result["soc"], 
        energy=result["energy"], 
        zip=zip
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
