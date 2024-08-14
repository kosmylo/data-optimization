from flask import Flask, request, jsonify
import pandas as pd
from utils import schedule_battery, compute_soc_schedule 

app = Flask(__name__)

@app.route('/schedule', methods=['GET'])
def get_schedule():
    """
    Endpoint to retrieve the optimized battery schedule.

    Query Parameters:
    - soc-start (float): Initial state of charge of the battery (default: 20.0)
    - soc-max (float): Maximum state of charge allowed (default: 90.0)
    - soc-min (float): Minimum state of charge allowed (default: 10.0)
    - soc-target (float): Target state of charge at the end of the schedule (default: 90.0)
    - power-capacity (float): Maximum power capacity for charging/discharging (default: 10.0)
    - storage-capacity (float): Total storage capacity of the battery (default: 100.0)
    - conversion-efficiency (float): Efficiency of the charge/discharge process (default: 1.0)
    - top-up (boolean): If true, the schedule will aim to top up the battery to full capacity (default: false)

    Returns:
    - JSON object containing:
        - costs (float): Total cost of the schedule.
        - power_schedule (list of float): The power schedule over time.
        - soc_schedule (list of float): The state of charge over time.
    """
    
    try:
        # Extract parameters from query string
        soc_start = float(request.args.get('soc-start', 20.0))
        soc_max = float(request.args.get('soc-max', 90.0))
        soc_min = float(request.args.get('soc-min', 10.0))
        soc_target = float(request.args.get('soc-target', 90.0))
        power_capacity = float(request.args.get('power-capacity', 10.0))
        storage_capacity = float(request.args.get('storage-capacity', 100.0))
        conversion_efficiency = float(request.args.get('conversion-efficiency', 1.0))
        top_up = request.args.get('top-up', 'false').lower() == 'true'

        # Prepare the data
        raw_prices = dict(
            production=[7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6],
            consumption=[8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7],
        )

        prices = pd.DataFrame(raw_prices, index=pd.date_range("2000-01-01T00:00+01", periods=len(raw_prices["consumption"]), freq="1H", inclusive="left"))
        
        # Call the scheduling function
        costs, power_schedule = schedule_battery(
            prices=prices,
            soc_start=soc_start,
            soc_max=soc_max,
            soc_min=soc_min,
            soc_target=soc_target,
            storage_capacity=storage_capacity,
            power_capacity=power_capacity,
            conversion_efficiency=conversion_efficiency,
            top_up=top_up
        )
        
        soc_schedule = compute_soc_schedule(power_schedule, soc_start, conversion_efficiency)
        
        # Return the result as JSON
        return jsonify({
            'costs': costs,
            'power_schedule': power_schedule,
            'soc_schedule': soc_schedule
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)