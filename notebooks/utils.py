import pandas as pd


# Function to extract market values from generators
def market_values(n, carrier='onwind'):
    """
    Calculate the market values of a generator (specified by carrier) troughout all 181 market areas as the sum product
    of production and locational marginal prices divided by the sum of production
    Arguments:
        n: pypsa network
        carrier: energy carrier | working for following `carrier`: ['offwind-ac','onwind','solar', 'ror', 'offwind-dc', 'gas',
        'residential rural solar thermal', 'services rural solar thermal', 'residential urban decentral solar thermal',
        'services urban decentral solar thermal', 'urban central solar thermal', 'oil', 'solar rooftop']
        found in n.generators.carrier.unique().tolist()
    Returns:
        market value of carrier per region
    """

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


def market_values_links(n, carrier="H2 Electrolysis"):
    """
    Calculate the market values of a link (specified by carrier) throughout all 181 market areas as the sum product
    of production and locational marginal prices divided by the sum of production
    Arguments:
        n: pypsa network
        carrier: energy carrier or technology
    Returns:
        market value of carrier per region
    """

    # select all the links for specific carrier e.g. H2 Electrolysis p1 is the active power at branch 1 where the
    # energy flows to (from p0 to p1); value is negative for power feed-in
    gen = abs(n.links_t.p1.loc[:, n.links.carrier == carrier])
    # create index from the generators and use as column names
    gen.columns = gen.columns.map(n.links.bus1)
    # sum up values at the same bus
    gen = gen.groupby(gen.columns, axis=1).sum()
    # get locational marginal prices for all locations and all time steps
    lmp = n.buses_t.marginal_price.loc[:, gen.columns]
    # calculate market values as sum product of generation times lmp divided by total generation
    mv = (gen * lmp).sum() / gen.sum()
    # set location of the buses/nodes as the index -> shape = (n_links x 1) 1 col with mvs
    mv.index = mv.index.map(n.buses.location)
    return mv


def market_values_links_con(n, carrier="H2 Electrolysis"):
    """
    Calculate the market values of the consumption of a link (specified by carrier) throughout all 181 market areas
    as the sum product of consumption and locational marginal prices of consumption source  divided by the sum of
    consumption
    Arguments:
        n: pypsa network
        carrier: energy carrier or technology
    Returns:
        consumption market value of carrier per region
    """

    con = n.links_t.p0.loc[:, n.links.carrier == carrier]
    con.columns = con.columns.map(n.links.bus0)
    lmp = n.buses_t.marginal_price.loc[:, con.columns]
    mv = (con * lmp).sum() / con.sum()
    mv.index = mv.index.map(n.buses.location)
    return mv


def congestion_rent_link(n, carrier="H2 Electrolysis"):
    """
    Calculate the differences in active power times lmp of node 0 and active power times lmp at node 1 where
    a link connects node 0 and 1. Difficulty: Links can have multiple inputs and outputs which all have to be considered
    Arguments:
        n: pypsa network
        carrier: energy carrier or technology
    Returns:
        congestion rent for every link/line and region
    """
    buses = ["bus0", "bus1", "bus2", "bus3", "bus4"]
    ps = ["p0", "p1", "p2", "p3", "p4"]
    cr = 0

    for bus, p in zip(buses, ps):
        if n.links[n.links.carrier == carrier][bus][0] != "":
            cr -= n.links_t[p].loc[:, n.links.carrier == carrier].multiply(
                n.buses_t.marginal_price[n.links[bus][n.links.carrier == carrier]].values)
    return cr


