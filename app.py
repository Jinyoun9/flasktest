import pybamm
import matplotlib.pyplot as plt
import numpy as np
import io
import os
import base64
from flask import Flask, request, render_template, send_file, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def run_pybaMM_simulation(params):
    # Define the lithium-ion battery model
    model = pybamm.lithium_ion.DFN()

    # Set parameter values using Chen2020 as a base and updating with user input
    param_values = pybamm.ParameterValues("Chen2020")
    param_values.update(params, check_already_exists=False)

    # Experiment setup with user-defined parameters
    experiment = pybamm.Experiment([
        (
            f"Discharge at {params['discharge_rate']}C until {params['voltage_min']}V",
            f"Charge at {params['charge_rate']}C until {params['voltage_max']}V",
            "Rest for 1 hour"
        )
    ], temperature=params['ambient_temp'])

    # Run the simulation
    sim = pybamm.Simulation(model, experiment=experiment, parameter_values=param_values)
    solution = sim.solve()

    # Generate example data for plotting
    cycle_cycs = list(range(1, 101))
    cycle_caps = [np.random.uniform(1, 2) for _ in cycle_cycs]
    charge_caps = [np.random.uniform(1, 2) for _ in cycle_cycs]
    coulombic_efficiencies = [np.random.uniform(90, 100) for _ in cycle_cycs]

    return cycle_cycs, cycle_caps, charge_caps, coulombic_efficiencies

@app.route('/')
def home():
    return render_template('index.html')  # Ensure this template contains your input form

@app.route('/simulate', methods=['POST'])
def simulate():
    # Collect user input from the form
    params = {
        'ambient_temp': float(request.form.get('ambient_temp', 298.15)),
        'faraday_constant': float(request.form.get('faraday_constant', 96485)),
        'current_function': float(request.form.get('current_function', 1.0)),
        'voltage_min': float(request.form.get('voltage_min', 2.5)),
        'voltage_max': float(request.form.get('voltage_max', 4.2)),
        'cell_capacity': float(request.form.get('cell_capacity', 5.0)),
        'reference_temp': float(request.form.get('reference_temp', 298.15)),
        'neg_electrode_thickness': float(request.form.get('neg_electrode_thickness', 1.0e-5)),
        'pos_electrode_thickness': float(request.form.get('pos_electrode_thickness', 1.0e-5)),
        'neg_electrode_conductivity': float(request.form.get('neg_electrode_conductivity', 215)),
        'pos_electrode_conductivity': float(request.form.get('pos_electrode_conductivity', 0.2)),
        'neg_electrode_density': float(request.form.get('neg_electrode_density', 1700)),
        'pos_electrode_density': float(request.form.get('pos_electrode_density', 3250)),
        'neg_electrode_volume_fraction': float(request.form.get('neg_electrode_volume_fraction', 0.75)),
        'pos_electrode_volume_fraction': float(request.form.get('pos_electrode_volume_fraction', 0.65)),
        'max_concentration_neg': float(request.form.get('max_concentration_neg', 32000)),
        'max_concentration_pos': float(request.form.get('max_concentration_pos', 62000)),
        'charge_rate': float(request.form.get('charge_rate', 1.0)),
        'discharge_rate': float(request.form.get('discharge_rate', 1.0))
    }

    # Run the simulation
    cycle_cycs, cycle_caps, charge_caps, coulombic_efficiencies = run_pybaMM_simulation(params)

    # Create subplots for the three graphs
    fig, axs = plt.subplots(3, 1, figsize=(12, 18))

    # Plot discharge capacity
    axs[0].plot(cycle_cycs, cycle_caps, marker='x', color='blue', label="Discharge Capacity [Ah/g]")
    axs[0].set_xlabel("Cycle Number")
    axs[0].set_ylabel("Discharge Capacity [Ah/g]")
    axs[0].set_title("Cycle Number vs Discharge Capacity")
    axs[0].legend()
    axs[0].grid(True)

    # Plot charge capacity
    axs[1].plot(cycle_cycs, charge_caps, marker='o', color='orange', label="Charge Capacity [Ah/g]")
    axs[1].set_xlabel("Cycle Number")
    axs[1].set_ylabel("Charge Capacity [Ah/g]")
    axs[1].set_title("Cycle Number vs Charge Capacity")
    axs[1].legend()
    axs[1].grid(True)

    # Plot coulombic efficiency
    axs[2].plot(cycle_cycs, coulombic_efficiencies, marker='^', color='green', label="Coulombic Efficiency [%]")
    axs[2].set_xlabel("Cycle Number")
    axs[2].set_ylabel("Coulombic Efficiency [%]")
    axs[2].set_title("Cycle Number vs Coulombic Efficiency")
    axs[2].legend()
    axs[2].grid(True)

    # Adjust layout and render the plot
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Convert the image to a base64 string
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Return the image data as JSON
    return {'imgData': img_base64}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
