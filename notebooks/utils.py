import pandas as pd
# Function to extract market values
# working for following `carrier`: "onwind", "solar", "solar rooftop", "offwind-dc", "offwind-ac".

def market_values(n, carrier="onwind"):
    # select all the generators for specific carrier e.g. onwind
    gen = n.generators_t.p.loc[:, n.generators.carrier == carrier]
    # create index from the generators and use as column names
    gen.columns = gen.columns.map(n.generators.bus)
    # get locational marginal prices for all locations and all time steps
    lmp = n.buses_t.marginal_price.loc[:, gen.columns]
    # calculate market values as sum product of generation times lmp divided by total generation
    mv = (gen * lmp).sum() / gen.sum()
    # set location of the buses/nodes as the index -> shape = (n_generators x 1) 1 col with mvs
    mv.index = mv.index.map(n.buses.location)
    return mv

def market_values_by_time_index(n, my_dates, carrier="onwind"):

    result = pd.DataFrame(index=my_dates, columns=n.buses.location.unique())
    for my_date in my_dates:
        # select all the generators for specific carrier e.g. onwind
        gen = n.generators_t.p.loc[n.generators_t.p.index.date == my_date.date(), n.generators.carrier == carrier]
        # create index from the generators and use as column names
        gen.columns = gen.columns.map(n.generators.bus)
        # get locational marginal prices for all locations and all time steps
        lmp = n.buses_t.marginal_price.loc[n.generators_t.p.index.date == my_date.date(), gen.columns]
        # calculate market values as sum product of generation times lmp divided by total generation
        mv = (gen * lmp).sum() / gen.sum()
        # set location of the buses/nodes as the index -> shape = (n_generators x 1) 1 col with mvs
        mv.index = mv.index.map(n.buses.location)

        # assign values to result
        for location in mv.index:
            result.loc[result.index == my_date, location] = mv[location]

    return result
