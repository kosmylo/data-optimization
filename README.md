# Battery Schedule Optimizer

This project provides an API for optimizing the charge and discharge schedule of a battery, given a set of consumption and production prices. The API includes a feature for topping up the battery to its full capacity.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

Ensure you have the required Python version and pip installed on your machine.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/kosmylo/data-optimization.git
   cd data-optimization
   ```

2. Set up a virtual environment:

   ```bash
   python -m venv venv
   ```

   This creates a virtual environment named venv in your project directory.

3. Activate the virtual environment:

   - On **macOS/Linux**:

     ```bash
     source venv/bin/activate
     ```

   - On **Windows**:

     ```bash
     venv\Scripts\activate
     ```

   After activating the virtual environment, your command prompt should change to indicate that you're now working inside the `venv`.

4. Install the dependencies:
    
    ```bash
    pip install -r requirements.txt
    ```
    This will install the necessary Python packages, including Flask, Pyomo, and other dependencies.

## Running the Application

To start the Flask server, run:

```bash
python battery_schedule.py
```

The server will start on http://127.0.0.1:5000/. You can then interact with the API using a tool like curl or Postman.

## API Endpoint

## GET `/schedule`

Retrieve the optimized battery schedule.

**Parameters**:

- `soc-start` (float, optional): Initial state of charge of the battery (default: 20.0).
- `soc-max` (float, optional): Maximum state of charge allowed (default: 90.0).
- `soc-min` (float, optional): Minimum state of charge allowed (default: 10.0).
- `soc-target` (float, optional): Target state of charge at the end of the schedule (default: 90.0).
- `power-capacity` (float, optional): Maximum power capacity for charging/discharging (default: 10.0).
- `storage-capacity` (float, optional): Total storage capacity of the battery (default: 100.0).
- `conversion-efficiency` (float, optional): Efficiency of the charge/discharge process (default: 1.0).
- `top-up` (boolean, optional): If true, the schedule will aim to top up the battery to full capacity (default: false).

**Example Request**:

```bash
curl "http://127.0.0.1:5000/schedule?soc-start=20&soc-max=90&soc-min=10&soc-target=90&power-capacity=10&storage-capacity=100&conversion-efficiency=1&top-up=true"
```

**Example Response**:

```json
{
    "costs": 100.0,
    "power_schedule": [10.0, -5.0, 10.0, 5.0, -10.0, ...],
    "soc_schedule": [20.0, 30.0, 20.0, 25.0, 15.0, ...]
}
```

**Error Handling**:

- If a **`ValueError`** is encountered (e.g., due to invalid input parameters like an infeasible SoC target), the API will return a `400` status code with a JSON error message explaining the specific issue.
- If a **`RuntimeError`** occurs (e.g., due to issues during the optimization process), the API will return a `500` status code with a JSON error message detailing the problem.
- If any other unexpected exception occurs, the API will return a `500` status code with a generic JSON error message indicating that an unexpected error occurred.

## Running Tests

To run the unit tests and API tests, execute:

```bash
bash ./run_tests.sh
```

This will run all the tests defined in test_scheduler.py and test_api.py.

## Top-Up Feature

When the top-up parameter is set to true, the API will aim to charge the battery to its full storage capacity by the end of the schedule. This feature is particularly useful when you want to ensure the battery is fully charged for a future period of expected high demand.

If top-up is false, the battery will aim to reach the soc-target defined by the user, but it will not try to reach full capacity.