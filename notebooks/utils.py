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


def generation(n, carrier='onwind'):
    """
    Calculate the generation of a generator (specified by carrier) troughout all 181 market areas as the sum
    Arguments:
        n: pypsa network
        carrier: energy carrier | working for following `carrier`: ['offwind-ac','onwind','solar', 'ror', 'offwind-dc', 'gas',
        'residential rural solar thermal', 'services rural solar thermal', 'residential urban decentral solar thermal',
        'services urban decentral solar thermal', 'urban central solar thermal', 'oil', 'solar rooftop']
        found in n.generators.carrier.unique().tolist()
    Returns:
        production of generator spcified by carrier per region
    """

    gen = n.generators_t.p.loc[:, n.generators.carrier == carrier]
    gen.columns = gen.columns.map(n.generators.bus)
    gen.columns = gen.columns.map(n.buses.location)
    gen = gen.sum()

    return gen


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

    result = result.apply(pd.to_numeric)

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

def generation_links(n, carrier="H2 Electrolysis"):
    """
    Calculate the generation of a link (specified by carrier) throughout all 181 market areas as the sum
    Arguments:
        n: pypsa network
        carrier: energy carrier or technology
    Returns:
        generation of carrier per region
    """

    gen = abs(n.links_t.p1.loc[:, n.links.carrier == carrier])
    gen.columns = gen.columns.map(n.links.bus1)
    gen = gen.groupby(gen.columns, axis=1).sum()
    gen.columns = gen.columns.map(n.buses.location)
    gen = gen.sum()
    return gen


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

def market_values_storage_units(n, carrier="hydro"):
    """
    Calculate the market values of the generation of a storage unit (specified by carrier) throughout all 181 market
    areas as the sum product of generation / dispatch and locational marginal prices of consumption bus divided by
    the sum of generation

    Arguments:
        n: pypsa network
        carrier: energy carrier or technology
    Returns:
        market value of carrier per region
    """
    # only take dispatched energy not stored
    gen = n.storage_units_t.p_dispatch.loc[:, n.storage_units.carrier == carrier]
    gen.columns = gen.columns.map(n.storage_units.bus)
    lmp = n.buses_t.marginal_price.loc[:, gen.columns]
    mv = (gen * lmp).sum() / gen.sum()
    mv.index = mv.index.map(n.buses.location)
    return mv

def generation_storage_units(n, carrier='hydro'):
    """
    Calculate the generation (=dispatch) of a storage unit (specified by carrier) troughout all 181 market areas as the sum
    Arguments:
        n: pypsa network
        carrier: energy carrier | working for following `carrier`: ['offwind-ac','onwind','solar', 'ror', 'offwind-dc', 'gas',
        'residential rural solar thermal', 'services rural solar thermal', 'residential urban decentral solar thermal',
        'services urban decentral solar thermal', 'urban central solar thermal', 'oil', 'solar rooftop']
        found in n.generators.carrier.unique().tolist()
    Returns:
        production of generator spcified by carrier per region
    """
    gen = n.storage_units_t.p_dispatch.loc[:, n.storage_units.carrier == carrier]
    gen.columns = gen.columns.map(n.storage_units.bus)
    gen.columns = gen.columns.map(n.buses.location)
    gen = gen.sum()
    return gen

# mapping of country code
convert_ISO_3166_2_to_1 = {
'AF':'AFG',
'AX':'ALA',
'AL':'ALB',
'DZ':'DZA',
'AS':'ASM',
'AD':'AND',
'AO':'AGO',
'AI':'AIA',
'AQ':'ATA',
'AG':'ATG',
'AR':'ARG',
'AM':'ARM',
'AW':'ABW',
'AU':'AUS',
'AT':'AUT',
'AZ':'AZE',
'BS':'BHS',
'BH':'BHR',
'BD':'BGD',
'BB':'BRB',
'BY':'BLR',
'BE':'BEL',
'BZ':'BLZ',
'BJ':'BEN',
'BM':'BMU',
'BT':'BTN',
'BO':'BOL',
'BA':'BIH',
'BW':'BWA',
'BV':'BVT',
'BR':'BRA',
'IO':'IOT',
'BN':'BRN',
'BG':'BGR',
'BF':'BFA',
'BI':'BDI',
'KH':'KHM',
'CM':'CMR',
'CA':'CAN',
'CV':'CPV',
'KY':'CYM',
'CF':'CAF',
'TD':'TCD',
'CL':'CHL',
'CN':'CHN',
'CX':'CXR',
'CC':'CCK',
'CO':'COL',
'KM':'COM',
'CG':'COG',
'CD':'COD',
'CK':'COK',
'CR':'CRI',
'CI':'CIV',
'HR':'HRV',
'CU':'CUB',
'CY':'CYP',
'CZ':'CZE',
'DK':'DNK',
'DJ':'DJI',
'DM':'DMA',
'DO':'DOM',
'EC':'ECU',
'EG':'EGY',
'SV':'SLV',
'GQ':'GNQ',
'ER':'ERI',
'EE':'EST',
'ET':'ETH',
'FK':'FLK',
'FO':'FRO',
'FJ':'FJI',
'FI':'FIN',
'FR':'FRA',
'GF':'GUF',
'PF':'PYF',
'TF':'ATF',
'GA':'GAB',
'GM':'GMB',
'GE':'GEO',
'DE':'DEU',
'GH':'GHA',
'GI':'GIB',
'GR':'GRC',
'GL':'GRL',
'GD':'GRD',
'GP':'GLP',
'GU':'GUM',
'GT':'GTM',
'GG':'GGY',
'GN':'GIN',
'GW':'GNB',
'GY':'GUY',
'HT':'HTI',
'HM':'HMD',
'VA':'VAT',
'HN':'HND',
'HK':'HKG',
'HU':'HUN',
'IS':'ISL',
'IN':'IND',
'ID':'IDN',
'IR':'IRN',
'IQ':'IRQ',
'IE':'IRL',
'IM':'IMN',
'IL':'ISR',
'IT':'ITA',
'JM':'JAM',
'JP':'JPN',
'JE':'JEY',
'JO':'JOR',
'KZ':'KAZ',
'KE':'KEN',
'KI':'KIR',
'KP':'PRK',
'KR':'KOR',
'KW':'KWT',
'KG':'KGZ',
'LA':'LAO',
'LV':'LVA',
'LB':'LBN',
'LS':'LSO',
'LR':'LBR',
'LY':'LBY',
'LI':'LIE',
'LT':'LTU',
'LU':'LUX',
'MO':'MAC',
'MK':'MKD',
'MG':'MDG',
'MW':'MWI',
'MY':'MYS',
'MV':'MDV',
'ML':'MLI',
'MT':'MLT',
'MH':'MHL',
'MQ':'MTQ',
'MR':'MRT',
'MU':'MUS',
'YT':'MYT',
'MX':'MEX',
'FM':'FSM',
'MD':'MDA',
'MC':'MCO',
'MN':'MNG',
'ME':'MNE',
'MS':'MSR',
'MA':'MAR',
'MZ':'MOZ',
'MM':'MMR',
'NA':'NAM',
'NR':'NRU',
'NP':'NPL',
'NL':'NLD',
'AN':'ANT',
'NC':'NCL',
'NZ':'NZL',
'NI':'NIC',
'NE':'NER',
'NG':'NGA',
'NU':'NIU',
'NF':'NFK',
'MP':'MNP',
'NO':'NOR',
'OM':'OMN',
'PK':'PAK',
'PW':'PLW',
'PS':'PSE',
'PA':'PAN',
'PG':'PNG',
'PY':'PRY',
'PE':'PER',
'PH':'PHL',
'PN':'PCN',
'PL':'POL',
'PT':'PRT',
'PR':'PRI',
'QA':'QAT',
'RE':'REU',
'RO':'ROU',
'RU':'RUS',
'RW':'RWA',
'BL':'BLM',
'SH':'SHN',
'KN':'KNA',
'LC':'LCA',
'MF':'MAF',
'PM':'SPM',
'VC':'VCT',
'WS':'WSM',
'SM':'SMR',
'ST':'STP',
'SA':'SAU',
'SN':'SEN',
'RS':'SRB',
'SC':'SYC',
'SL':'SLE',
'SG':'SGP',
'SK':'SVK',
'SI':'SVN',
'SB':'SLB',
'SO':'SOM',
'ZA':'ZAF',
'GS':'SGS',
'ES':'ESP',
'LK':'LKA',
'SD':'SDN',
'SR':'SUR',
'SJ':'SJM',
'SZ':'SWZ',
'SE':'SWE',
'CH':'CHE',
'SY':'SYR',
'TW':'TWN',
'TJ':'TJK',
'TZ':'TZA',
'TH':'THA',
'TL':'TLS',
'TG':'TGO',
'TK':'TKL',
'TO':'TON',
'TT':'TTO',
'TN':'TUN',
'TR':'TUR',
'TM':'TKM',
'TC':'TCA',
'TV':'TUV',
'UG':'UGA',
'UA':'UKR',
'AE':'ARE',
'GB':'GBR',
'US':'USA',
'UM':'UMI',
'UY':'URY',
'UZ':'UZB',
'VU':'VUT',
'VE':'VEN',
'VN':'VNM',
'VG':'VGB',
'VI':'VIR',
'WF':'WLF',
'EH':'ESH',
'YE':'YEM',
'ZM':'ZMB',
'ZW':'ZWE'
}
