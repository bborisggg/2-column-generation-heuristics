# Single-shift petrol replenishment: benchmark instances

Ten semi-synthetic instances (`seed_130.txt` … `seed_139.txt`) of a single-shift fuel
replenishment problem: a heterogeneous fleet of tanker trucks must refill underground reservoirs
at petrol stations within one shift. They are derived from real operational data of a Russian fuel
distributor; the road network is the same in all ten, and the instances differ in the demand draw.

`read_instance.py` is a reference reader — the format specification in executable form. It consumes
the whole token stream and asserts that nothing is left over:

```
python3 read_instance.py seed_130.txt
```

## The problem

One planning shift of `H` minutes. Each **truck** has compartments and hoses. Every compartment is
filled to capacity at the depot and its entire content is poured into exactly one reservoir, so
deliveries are discrete: a reservoir receives the sum of the capacities of the compartments assigned
to it. Hoses allow several compartments to be discharged in parallel at one stop. A truck may run at
most two trips per shift, and its total time (travel, loading, station setup, filling) must fit in
its shift length.

Each **station** holds several reservoirs. A reservoir is filled on a single trip — its delivery
cannot be split across trips or trucks — but a station may be visited more than once, by different
trips or trucks. Two trucks may **not** unload at the same station at overlapping times.

Reservoirs are consumed during the shift at known hourly rates, so the free space in a reservoir —
and hence the largest delivery it can accept — grows with the arrival time, while its level must
never drop below a safety minimum. A reservoir with a positive demand lower bound is **class B** and
must be served; one with a zero lower bound is **class A** and may be served or not.

**Objective:** serve every class-B reservoir using a minimum-weight set of trucks, i.e. minimise
`sum_k c_k * y_k`, where `y_k = 1` if truck `k` is used. In these instances every `c_k = 1`, so the
objective is simply the number of trucks used. (Weights let owned trucks be preferred over rented
ones.)

## File format

Whitespace-separated numbers, read as one token stream; line breaks carry no meaning. In order:

| # | Tokens | Meaning |
|---|---|---|
| 1 | `num_stations H phi num_trucks` | station count; shift horizon in minutes; minutes to move 1000 litres; truck count |
| 2 | `d_dual d_next` | optional side constraints, see below |
| 3 | `total_gen random_choice_prob` | parameters of *our* solver, not instance data — ignore |
| 4 | per truck, `num_trucks` blocks | `num_compartments max_stations_per_route neighbourhood shift num_hoses pre_loaded cost`, then `num_compartments` compartment capacities in litres |
| 5 | per station, `num_stations` blocks | `num_reservoirs setup_time depot_to_station station_to_depot`, then per reservoir: `initial min_level capacity demand_lower demand_upper` followed by `H/60` hourly consumption rates (litres/hour, may be fractional) |
| 6 | `num_stations × num_stations` | station-to-station travel times in minutes, row-major |
| 7 | `num_trucks × num_stations` | compatibility, `1` = truck may serve that station |


### Derived quantities, as our solver interprets the data

- **Reservoir indexing**: flatten stations in file order into a global reservoir list (181 here);
  reservoir `i` belongs to station `st(i)`.
- **Travel between reservoirs**: `0` if the same station, else `travel[st(i)][st(j)]`; an arc is
  usable only if that value is `< H`.
- **Loading time**: `floor(sum(capacities) * phi / 1000)` minutes for a full load.
- **Stop time**: `setup_time(station)` plus the filling time, which is the **maximum over hoses** of
  `litres_on_that_hose * phi / 1000` (compartments are assigned to hoses to balance the load).
- **Dynamic reserves**: `level(t) = initial - consumed(0, t)` from the hourly rates. At the arrival
  time the level must be `>= min_level`, and the delivery must fit the free space,
  `delivery <= capacity - level(arrival)`.
- **Delivery window** per reservoir: `[max(1, demand_lower), min(demand_upper, capacity - min_level)]`.
  It is non-empty for every reservoir in all ten instances.
- **Unloading order**: the compartment nearest the cab must be emptied last.

### The two optional side constraints (block 2)

`d_dual` requires at least that many trucks to run **two** trips in the shift; `d_next` requires at
least that many trucks to **finish the shift loaded**, ready for the next one. The shipped values are
`1` and `0`. Both are specific to our study — set them to `0` to ignore them; doing so only relaxes
the problem, and the best known values below were obtained with the shipped values.

## The instances

All ten share: 69 stations, 181 reservoirs, 34 trucks, `H = 720` minutes, `phi = 3`,
`max_stations_per_route = 3`, `neighbourhood = 1000`; truck shifts 181–719 minutes; 4 or 5
compartments and 2 hoses per truck; total truck capacity 27 785–34 490 litres; every truck
pre-loaded, with cost 1 and its own compatibility row; station setup times 40–70 minutes; usable
travel times 0–300 minutes.

They differ only in the demand draw, hence in how many reservoirs are class B:

| instance | class B (must serve) | class A (optional) |
|---|---|---|
| seed_130 | 69 | 112 |
| seed_131 | 62 | 119 |
| seed_132 | 72 | 109 |
| seed_133 | 53 | 128 |
| seed_134 | 65 | 116 |
| seed_135 | 60 | 121 |
| seed_136 | 67 | 114 |
| seed_137 | 68 | 113 |
| seed_138 | 71 | 110 |
| seed_139 | 61 | 120 |

## Best known results

Objective = number of trucks used, with every class-B reservoir served.

| instance | best solution found | best lower bound | gap |
|---|---|---|---|
| seed_130 | 13 | 13 | closed |
| seed_131 | 13 | 12 | 1 |
| seed_132 | 14 | 14 | closed |
| seed_133 | 10 | 10 | closed |
| seed_134 | 13 | 13 | closed |
| seed_135 | 12 | 12 | closed |
| seed_136 | 13 | 13 | closed |
| seed_137 | 14 | 14 | closed |
| seed_138 | 14 | 14 | closed |
| seed_139 | 13 | 12 | 1 |

The bounds are the LP relaxation of a set-partitioning master over daily plans built from the
complete set of routes visiting at most three stations, rounded up, obtained by column generation.

If your solver permits unserved class-B reservoirs, note that ours charges a penalty of 1000 each, so
objective values of the form `1000 * u + trucks` encode `u` unserved reservoirs. Every value in the
table has `u = 0`.
