from __future__ import annotations
import numpy as np
import pandas as pd
from pyomo.core import (
    ConcreteModel,
    Var,
    RangeSet,
    Param,
    Reals,
    NonNegativeReals,
    NonPositiveReals,
    Constraint,
    Objective,
    minimize
)
from pyomo.environ import value
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

def compute_soc_schedule(power_schedule: list[float], soc_start: float, conversion_efficiency: float) -> list[float]:
    """Determine the scheduled state of charge (SoC), given a power schedule and a starting SoC.

    :param power_schedule:          List of power changes (positive for charging, negative for discharging).
    :param soc_start:               Initial state of charge at the beginning of the schedule.
    :param conversion_efficiency:   Efficiency of the charge/discharge process. 
    """
    
    adjusted__power_schedule = [power * conversion_efficiency if power > 0 else power / conversion_efficiency for power in power_schedule]
    return [soc_start] + list(np.cumsum(adjusted__power_schedule) + soc_start)

def schedule_battery(
    prices: pd.DataFrame,
    soc_start: float,
    soc_max: float,
    soc_min: float,
    soc_target: float,
    power_capacity: float,
    storage_capacity: float,
    conversion_efficiency: float,
    top_up: bool
) -> tuple[float, list[float]]:
    """Schedule a battery against given consumption and production prices.
    
    :param prices:                  Pandas DataFrame with columns "consumption" and "production" containing prices.
    :param soc_start:               State of charge at the start of the schedule.
    :param soc_max:                 Maximum state of charge.
    :param soc_min:                 Minimum state of charge.
    :param soc_target:              Target state of charge at the end of the schedule.
    :param power_capacity:          Power capacity for both charging and discharging.
    :param storage_capacity:        Storage capacity of the battery.
    :param conversion_efficiency:   Conversion efficiency from power to SoC and vice versa.
    :param top_up:                  Boolean flag to indicate if top-up to full capacity is required.
    """
    
    # Pre-check logical constraints before running the optimization

    # Check if SOC min and max make sense
    if soc_min >= soc_max:
        raise ValueError(f"soc_min ({soc_min}%) must be less than soc_max ({soc_max}%)")

    # Check if SOC start is within bounds
    if not (soc_min <= soc_start <= soc_max):
        raise ValueError(f"soc_start ({soc_start}%) must be between soc_min ({soc_min}%) and soc_max ({soc_max}%)")

    # Check if the SOC target is achievable given the SOC start, storage, and power capacity
    if soc_target > storage_capacity:
        raise ValueError(f"soc_target ({soc_target} kWh) cannot exceed storage_capacity ({storage_capacity} kWh)")

    if soc_target < soc_min or soc_target > soc_max:
        raise ValueError(f"soc_target ({soc_target}%) must be between soc_min ({soc_min}%) and soc_max ({soc_max}%)")

    if power_capacity <= 0:
        raise ValueError(f"power_capacity ({power_capacity} kW) must be positive")

    model = ConcreteModel()
    model.j = RangeSet(0, len(prices.index.to_pydatetime()) - 1, doc="Set of datetimes")
    model.ems_power = Var(model.j, domain=Reals, initialize=0)
    model.device_power_down = Var(model.j, domain=NonPositiveReals, initialize=0)
    model.device_power_up = Var(model.j, domain=NonNegativeReals, initialize=0)

    def price_up_select(m, j):
        return prices["consumption"].iloc[j]

    def price_down_select(m, j):
        return prices["production"].iloc[j]

    model.up_price = Param(model.j, initialize=price_up_select)
    model.down_price = Param(model.j, initialize=price_down_select)

    model.device_max = Param(model.j, initialize=soc_max)
    model.device_min = Param(model.j, initialize=soc_min)

    def ems_derivative_bounds(m, j):
        return (
            -power_capacity,
            m.ems_power[j],
            power_capacity,
        )
    
    def device_bounds(m, j):
        stock_changes = [
            (
                m.device_power_down[k] / conversion_efficiency  
                + m.device_power_up[k] * conversion_efficiency 
            )
            for k in range(0, j + 1)
        ]

        if top_up:
            # If it's the last time step, the SoC should be exactly the storage_capacity
            if j == len(prices) - 1:
                return (
                    storage_capacity,
                    soc_start + sum(stock_changes),
                    storage_capacity,
                )
            else:
                # During other times, SoC should be below 90% of the storage capacity
                return (
                    m.device_min[j],
                    soc_start + sum(stock_changes),
                    m.device_max[j],
                )
        else:   
            # Apply soc target and bounds when top_up is false
            if j == len(prices) - 1:
                return (
                    soc_target,
                    soc_start + sum(stock_changes),
                    soc_target,
                )

            # Stay within SoC bounds (soc_min and soc_max)
            return (
                m.device_min[j],
                soc_start + sum(stock_changes),
                m.device_max[j],
            )

    def device_derivative_equalities(m, j):
        """Determine aggregate flow ems_power."""
        return (
            0,
            m.device_power_up[j] + m.device_power_down[j] - m.ems_power[j],
            0,
        )

    model.device_power_up_bounds = Constraint(model.j, rule=ems_derivative_bounds)
    model.device_power_equalities = Constraint(model.j, rule=device_derivative_equalities)
    model.device_energy_bounds = Constraint(model.j, rule=device_bounds)

    # Add objective
    def cost_function(m):
        costs = 0
        for j in m.j:
            costs += m.device_power_down[j] * m.down_price[j]
            costs += m.device_power_up[j] * m.up_price[j]
        return costs

    model.costs = Objective(rule=cost_function, sense=minimize)
    solver = SolverFactory("appsi_highs")
    results = solver.solve(model, load_solutions=False)
    print(results.solver.termination_condition)

    # Check for infeasibility
    if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
        model.solutions.load_from(results)
        planned_costs = value(model.costs)
        planned_device_power = [model.ems_power[j].value for j in model.j]
        return planned_costs, planned_device_power
    elif results.solver.termination_condition == TerminationCondition.infeasible:
        raise ValueError("The optimization problem is infeasible with the given parameters. Possible causes could be: "
                         "1) The power capacity is insufficient to meet the target SoC. "
                         "2) The target SoC is not achievable given the initial state and other constraints. "
                         "3) Conflicting constraints make the problem unsolvable.")
    else:
        raise RuntimeError(f"Solver failed with termination condition: {results.solver.termination_condition}")